import os
import signal
import subprocess
import tempfile
from datetime import datetime
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
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


def verify_admin_token(token: str = Query(None)):
    """Allow downloading backup using query token or Authorization header."""
    if not token:
        raise HTTPException(status_code=401, detail="Authentication token required")
    payload = get_admin_payload(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


@router.get("/backup")
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

    cmd = [
        "pg_dump",
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

        if proc.returncode != 0:
            logger.error(f"pg_dump error: {proc.stderr}")
            raise HTTPException(
                status_code=500, detail=f"Database dump failed: {proc.stderr}"
            )

        return FileResponse(
            path=backup_file_path,
            filename="backup.sql",
            media_type="application/sql",
        )
    except Exception as e:
        logger.error(f"Backup exception: {e}")
        if os.path.exists(backup_file_path):
            os.remove(backup_file_path)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restore")
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

    # Save uploaded file to temp location
    temp_dir = tempfile.gettempdir()
    restore_file_path = os.path.join(temp_dir, f"restore_{datetime.utcnow().timestamp()}.sql")

    try:
        content = await file.read()
        if len(content) < 10:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        with open(restore_file_path, "wb") as f:
            f.write(content)

        # Execute psql to restore
        cmd = [
            "psql",
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

        proc = subprocess.run(
            cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=180
        )

        if proc.returncode != 0:
            logger.error(f"psql restore error: {proc.stderr}")
            raise HTTPException(
                status_code=500, detail=f"Database restore failed: {proc.stderr}"
            )

        logger.info("Database restore completed successfully")

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
