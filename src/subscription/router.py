import base64
import socket
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse

import src.accounts.service as account_service
from src import config
from src.database import get_db
from src.inbound_configs.service import get_inbound_configs
from src.subscription.template import (
    render_not_found_page,
    render_subscription_page,
)
from src.utils import xray

router = APIRouter()


def is_browser_request(request: Request) -> bool:
    """
    Differentiate between a human visiting in a browser vs a V2Ray / VPN client.
    """
    # 1. Query parameter overrides
    fmt = request.query_params.get("format", "").lower()
    if fmt in ["raw", "sub", "text", "v2ray"]:
        return False
    if request.query_params.get("plain", "").lower() in ["true", "1"]:
        return False
    if request.query_params.get("html", "").lower() in ["true", "1"] or fmt == "html":
        return True

    user_agent = request.headers.get("user-agent", "").lower()
    accept = request.headers.get("accept", "").lower()

    # 2. Known VPN / Proxy client User-Agents
    vpn_client_signatures = [
        "v2rayng",
        "v2rayn",
        "v2ray",
        "xray",
        "shadowrocket",
        "foxray",
        "streisand",
        "sing-box",
        "singbox",
        "sagernet",
        "nekobox",
        "nekoray",
        "clash",
        "stash",
        "surge",
        "quantumult",
        "loon",
        "surfboard",
        "karing",
        "v2box",
        "husi",
        "oneclick",
        "fair",
        "wings",
        "potatso",
        "passwall",
        "openwrt",
        "okhttp",
        "go-http-client",
        "curl",
        "wget",
        "python-requests",
        "urllib",
        "aiohttp",
    ]
    for sig in vpn_client_signatures:
        if sig in user_agent:
            return False

    # 3. Standard browser Accept header requests text/html
    if "text/html" in accept:
        return True

    # 4. Standard browser User-Agent patterns
    browser_signatures = [
        "mozilla",
        "chrome",
        "safari",
        "firefox",
        "edge",
        "opera",
        "android",
        "iphone",
        "ipad",
    ]
    if any(b in user_agent for b in browser_signatures):
        return True

    return False


def get_clean_sub_url(request: Request, uuid: str) -> str:
    """Resolve clean public subscription URL."""
    base = getattr(config, "SUBSCRIPTION_BASE_URL", "")
    if base and "localhost" not in base and "127.0.0.1" not in base:
        if base.endswith("/"):
            return f"{base}{uuid}"
        return f"{base}/{uuid}"
    # Otherwise use request url stripped of query params
    return str(request.url).split("?")[0]


@router.get("/sub/{uuid}", tags=["Subscription"])
def sub(
    request: Request,
    uuid: str,
    size: int = -1,
    plain: bool = False,
    resolve: bool = False,
    develop: bool = False,
    address: str = None,
    q: str = None,
    db: Session = Depends(get_db),
):
    browser_mode = is_browser_request(request)

    db_account = account_service.get_account_by_uuid(db=db, uuid=uuid)

    if not db_account:
        if browser_mode:
            return HTMLResponse(content=render_not_found_page(uuid), status_code=404)
        raise HTTPException(status_code=404, detail="Account not found")

    inbound_configs, count = get_inbound_configs(
        db=db, host_zone_id=db_account.host_zone_id, q=q
    )

    rows = []
    nodes_info = []

    for inbound_config in inbound_configs:
        if (
            inbound_config.enable
            and inbound_config.inbound.enable
            and inbound_config.inbound.host.enable
            and (inbound_config.develop is not True or develop is True)
        ):
            if address:
                inbound_address = address
            else:
                inbound_address = inbound_config.address

            if resolve:
                inbound_address = _get_ip(inbound_address)
                remark = inbound_config.remark + " " + inbound_config.address
            else:
                remark = inbound_config.remark

            network_val = (
                inbound_config.network.value
                if hasattr(inbound_config.network, "value")
                else str(inbound_config.network)
            )
            security_val = (
                inbound_config.security.value
                if hasattr(inbound_config.security, "value")
                else str(inbound_config.security)
            )
            fp_val = (
                inbound_config.finger_print.value
                if hasattr(inbound_config.finger_print, "value")
                else str(inbound_config.finger_print)
            )

            link = xray.generate_vless_config(
                address=inbound_address,
                network_type=network_val,
                port=inbound_config.port,
                uuid=uuid,
                host=inbound_config.host,
                sni=inbound_config.sni,
                fp=fp_val,
                path=inbound_config.path,
                security=security_val,
                sid=inbound_config.sid,
                pbk=inbound_config.pbk,
                spx=inbound_config.spx,
                flow=(
                    inbound_config.inbound.flow.value
                    if inbound_config.inbound.flow
                    else None
                ),
                remark=remark,
                alpns=inbound_config.alpns,
            )
            rows.append(link)
            nodes_info.append(
                {
                    "remark": remark,
                    "network": network_val,
                    "security": security_val,
                    "port": inbound_config.port,
                    "address": inbound_address,
                    "link": link,
                }
            )

    # Format=json check
    if request.query_params.get("format") == "json":
        return JSONResponse(
            content={
                "uuid": uuid,
                "email": db_account.email,
                "user_title": db_account.user_title,
                "service_title": db_account.service_title,
                "enable": db_account.enable,
                "used_traffic": db_account.used_traffic,
                "data_limit": db_account.data_limit,
                "started_at": (
                    db_account.started_at.isoformat()
                    if db_account.started_at
                    else None
                ),
                "expired_at": (
                    db_account.expired_at.isoformat()
                    if db_account.expired_at
                    else None
                ),
                "servers_count": len(rows),
                "servers": nodes_info,
            }
        )

    # Check if this is a web browser request
    if browser_mode:
        sub_url = get_clean_sub_url(request, uuid)
        html_content = render_subscription_page(
            account=db_account,
            configs=rows,
            nodes_info=nodes_info,
            subscription_url=sub_url,
        )
        return HTMLResponse(content=html_content, status_code=200)

    # V2Ray / Proxy Client Response
    text = "\n".join(rows) + "\n"
    if not plain:
        content_bytes = base64.b64encode(text.encode("utf-8"))
    else:
        content_bytes = text.encode("utf-8")

    # Standard Subscription Headers for V2Ray clients
    upload = 0
    download = int(db_account.used_traffic or 0)
    total = int(db_account.data_limit or 0)
    expire = (
        int(db_account.expired_at.timestamp()) if db_account.expired_at else 0
    )

    profile_title = (
        db_account.user_title
        or db_account.service_title
        or db_account.email
        or "Elora"
    )
    safe_title_b64 = base64.b64encode(profile_title.encode("utf-8")).decode("ascii")

    headers = {
        "Subscription-Userinfo": f"upload={upload}; download={download}; total={total}; expire={expire}",
        "Profile-Update-Interval": "12",
        "Content-Disposition": f'inline; filename="{uuid}.txt"',
        "Profile-Title": f"base64:{safe_title_b64}",
    }

    return Response(
        content=content_bytes,
        media_type="text/plain; charset=utf-8",
        headers=headers,
    )


def _get_ip(d):
    """
    This method returns the first IP address string
    that responds as the given domain name
    """
    try:
        return socket.gethostbyname(d)
    except Exception:
        return d
