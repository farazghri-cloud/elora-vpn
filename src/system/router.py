import glob
import json
import os
import shutil
import signal
import subprocess
import tempfile
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from src.admins.schemas import Admin
from src.db_config import SQLALCHEMY_DATABASE_URL
from src.logger import logger
from src.system.version_manager import version_manager
from src.utils.jwt import get_admin_payload

router = APIRouter()


@router.get("/version")
async def get_version():
    """Get application version information."""
    return version_manager.get_version_info()


def verify_admin_token(request: Request, token: Optional[str] = Query(None)):
    """Allow downloading backup using query token or Authorization header."""
    raw_token = token
    if not raw_token:
        auth_header = request.headers.get("authorization")
        if auth_header:
            if auth_header.lower().startswith("bearer "):
                raw_token = auth_header[7:].strip()
            else:
                raw_token = auth_header.strip()

    if not raw_token:
        raise HTTPException(status_code=401, detail="Authentication token required")

    payload = get_admin_payload(raw_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload


def find_pg_tool(name: str) -> Optional[str]:
    """Locate PostgreSQL utility (pg_dump, psql) anywhere on the system."""
    p = shutil.which(name)
    if p:
        return p
    for candidate in [
        f"/usr/bin/{name}",
        f"/usr/local/bin/{name}",
        f"/bin/{name}",
        f"/opt/elora-vpn/venv/bin/{name}",
    ]:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    matches = glob.glob(f"/usr/lib/postgresql/*/bin/{name}")
    if matches:
        return sorted(matches)[-1]
    return None


def export_via_sqlalchemy(output_file_path: str):
    """Reliable pure-Python database exporter using active SQLAlchemy connection."""
    from sqlalchemy import inspect, text
    from src.database import engine

    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    with open(output_file_path, "w", encoding="utf-8") as out:
        out.write("-- BESTPRIME V2RAY Complete Database Backup\n")
        out.write(f"-- Generated: {datetime.utcnow().isoformat()} UTC\n\n")
        out.write("SET session_replication_role = 'replica';\n\n")

        with engine.connect() as conn:
            for table in table_names:
                cols = [col["name"] for col in inspector.get_columns(table)]
                if not cols:
                    continue
                quoted_cols = ", ".join([f'"{c}"' for c in cols])
                rows = conn.execute(text(f'SELECT {quoted_cols} FROM "{table}"')).fetchall()

                out.write(f'TRUNCATE TABLE "{table}" CASCADE;\n')
                if rows:
                    out.write(f'INSERT INTO "{table}" ({quoted_cols}) VALUES\n')
                    val_rows = []
                    for row in rows:
                        row_items = []
                        for item in row:
                            if item is None:
                                row_items.append("NULL")
                            elif isinstance(item, bool):
                                row_items.append("TRUE" if item else "FALSE")
                            elif isinstance(item, (int, float)):
                                row_items.append(str(item))
                            elif isinstance(item, (dict, list)):
                                escaped = json.dumps(item).replace("'", "''")
                                row_items.append(f"'{escaped}'")
                            elif hasattr(item, "isoformat"):
                                row_items.append(f"'{item.isoformat()}'")
                            else:
                                escaped = str(item).replace("'", "''")
                                row_items.append(f"'{escaped}'")
                        val_rows.append(f"  ({', '.join(row_items)})")
                    out.write(",\n".join(val_rows) + ";\n\n")

            # Sequence reset for serial/auto-increment columns
            for table in table_names:
                pk_constraint = inspector.get_pk_constraint(table)
                pks = pk_constraint.get("constrained_columns", [])
                if pks and len(pks) == 1:
                    pk = pks[0]
                    out.write("DO $$ BEGIN\n")
                    out.write(f"  PERFORM setval(pg_get_serial_sequence('"{table}"', '{pk}'), COALESCE((SELECT MAX("{pk}") FROM "{table}"), 1), true);\n")
                    out.write("EXCEPTION WHEN OTHERS THEN NULL;\nEND $$;\n\n")

            out.write("SET session_replication_role = 'origin';\n")


def import_via_sqlalchemy(input_file_path: str):
    """Reliable pure-Python database importer using active SQLAlchemy connection."""
    from sqlalchemy import text
    from src.database import engine

    with open(input_file_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    with engine.begin() as conn:
        conn.execute(text("SET session_replication_role = 'replica';"))
        conn.execute(text(sql_content))
        conn.execute(text("SET session_replication_role = 'origin';"))


@router.get("/backup")
@router.get("/system/backup")
def download_backup(payload: dict = Depends(verify_admin_token)):
    """Generate a clean PostgreSQL backup.sql file and send it as a download."""
    logger.info("Admin initiated database backup")

    parsed = urlparse(SQLALCHEMY_DATABASE_URL)
    db_name = parsed.path.lstrip("/")
    db_user = parsed.username or "elora"
    db_host = parsed.hostname or "localhost"
    db_port = str(parsed.port or 5432)
    db_pass = parsed.password or ""

    env = os.environ.copy()
    if db_pass:
        env["PGPASSWORD"] = db_pass

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_{timestamp}.sql"
    temp_dir = tempfile.gettempdir()
    backup_file_path = os.path.join(temp_dir, backup_filename)

    # 1. Try pg_dump first if available
    pg_dump_bin = find_pg_tool("pg_dump")
    dump_success = False

    if pg_dump_bin:
        cmd = [
            pg_dump_bin,
            "-h",
            db_host,
            "-p",
            db_port,
            "-U",
            db_user,
            "--clean",
            "--if-exists",
            "--no-owner",
            "--no-privileges",
            db_name,
        ]
        try:
            with open(backup_file_path, "w", encoding="utf-8") as out:
                proc = subprocess.run(
                    cmd, env=env, stdout=out, stderr=subprocess.PIPE, text=True, timeout=120
                )
            if proc.returncode == 0 and os.path.getsize(backup_file_path) > 0:
                dump_success = True
                logger.info("Backup successfully generated via pg_dump")
            else:
                logger.warning(f"pg_dump returned non-zero code {proc.returncode}: {proc.stderr}")
        except Exception as e:
            logger.warning(f"pg_dump execution failed: {e}")

    # 2. Seamless fallback to pure-Python SQLAlchemy export
    if not dump_success:
        try:
            logger.info("Exporting database backup via SQLAlchemy engine fallback...")
            export_via_sqlalchemy(backup_file_path)
            dump_success = True
            logger.info("Backup successfully generated via SQLAlchemy engine")
        except Exception as e:
            logger.error(f"SQLAlchemy export failed: {e}")
            if os.path.exists(backup_file_path):
                os.remove(backup_file_path)
            raise HTTPException(status_code=500, detail=f"Backup generation failed: {str(e)}")

    return FileResponse(
        path=backup_file_path,
        filename="backup.sql",
        media_type="application/sql",
    )


@router.post("/restore")
@router.post("/system/restore")
async def restore_backup(
    file: UploadFile = File(...),
    admin: Admin = Depends(Admin.get_current),
):
    """Restore database from an uploaded backup.sql file."""
    if not file.filename or not file.filename.endswith(".sql"):
        raise HTTPException(
            status_code=400, detail="Invalid file format. Please upload a .sql file"
        )

    logger.info(f"Admin restoring database from file: {file.filename}")

    parsed = urlparse(SQLALCHEMY_DATABASE_URL)
    db_name = parsed.path.lstrip("/")
    db_user = parsed.username or "elora"
    db_host = parsed.hostname or "localhost"
    db_port = str(parsed.port or 5432)
    db_pass = parsed.password or ""

    env = os.environ.copy()
    if db_pass:
        env["PGPASSWORD"] = db_pass

    temp_dir = tempfile.gettempdir()
    restore_file_path = os.path.join(temp_dir, f"restore_{datetime.utcnow().timestamp()}.sql")

    try:
        content = await file.read()
        if len(content) < 10:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        with open(restore_file_path, "wb") as f:
            f.write(content)

        restore_success = False

        # 1. Try psql if available
        psql_bin = find_pg_tool("psql")
        if psql_bin:
            cmd = [
                psql_bin,
                "-h",
                db_host,
                "-p",
                db_port,
                "-U",
                db_user,
                "-d",
                db_name,
                "-f",
                restore_file_path,
            ]
            try:
                proc = subprocess.run(
                    cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=180
                )
                if proc.returncode == 0:
                    restore_success = True
                    logger.info("Database restored successfully via psql")
                else:
                    logger.warning(f"psql restore failed ({proc.returncode}): {proc.stderr}")
            except Exception as e:
                logger.warning(f"psql command error: {e}")

        # 2. Fallback to SQLAlchemy engine restore
        if not restore_success:
            logger.info("Restoring database via SQLAlchemy engine fallback...")
            import_via_sqlalchemy(restore_file_path)
            restore_success = True
            logger.info("Database restored successfully via SQLAlchemy engine")

        logger.info("Database restore process finished successfully")

        # Automatically schedule reload
        try:
            os.kill(os.getpid(), signal.SIGTERM)
        except Exception:
            pass

        return JSONResponse(
            content={
                "message": "Database restored successfully. Server is restarting..."
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Restore exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(restore_file_path):
            try:
                os.remove(restore_file_path)
            except Exception:
                pass
