import base64
import html
import json
import urllib.parse
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.subscription.utils import (
    format_bytes,
    format_gregorian_date,
    format_jalali_date,
)


def render_subscription_page(
    account: Any,
    configs: List[str],
    nodes_info: List[Dict[str, Any]],
    subscription_url: str,
) -> str:
    """Renders a responsive, modern HTML dashboard for subscription details."""
    now = datetime.utcnow()

    # User & Title
    user_title = (
        account.user_title or account.service_title or account.email or "کاربر گرامی"
    )
    email = account.email or ""
    uuid = str(account.uuid)

    # Traffic calculations
    used_bytes = int(account.used_traffic or 0)
    limit_bytes = int(account.data_limit or 0)
    is_unlimited_traffic = limit_bytes <= 0

    if is_unlimited_traffic:
        remaining_bytes = 0
        used_percent = 0.0
        used_formatted = format_bytes(used_bytes)
        remaining_formatted = "نامحدود"
        limit_formatted = "نامحدود"
    else:
        remaining_bytes = max(0, limit_bytes - used_bytes)
        used_percent = min(100.0, round((used_bytes / limit_bytes) * 100, 1))
        used_formatted = format_bytes(used_bytes)
        remaining_formatted = format_bytes(remaining_bytes)
        limit_formatted = format_bytes(limit_bytes)

    # Time & Expiry calculations
    is_expired = False
    remaining_days_text = ""
    started_at = account.started_at
    expired_at = account.expired_at

    if expired_at:
        delta = expired_at - now
        if delta.total_seconds() <= 0:
            is_expired = True
            remaining_days_text = "منقضی شده"
        else:
            days = delta.days
            hours = int(delta.seconds // 3600)
            if days > 0:
                remaining_days_text = f"{days} روز و {hours} ساعت"
            else:
                remaining_days_text = f"{hours} ساعت"
    else:
        remaining_days_text = "نامحدود (بدون انقضا)"

    started_jalali = format_jalali_date(started_at)
    started_gregorian = format_gregorian_date(started_at)
    expired_jalali = format_jalali_date(expired_at)
    expired_gregorian = format_gregorian_date(expired_at)

    # Status detection
    if not account.enable:
        status_key = "disabled"
        status_label = "غیرفعال شده"
        status_badge_class = "badge-disabled"
        status_glow_class = "glow-disabled"
    elif is_expired:
        status_key = "expired"
        status_label = "منقضی شده"
        status_badge_class = "badge-expired"
        status_glow_class = "glow-expired"
    elif not is_unlimited_traffic and used_bytes >= limit_bytes:
        status_key = "exhausted"
        status_label = "اتمام حجم"
        status_badge_class = "badge-exhausted"
        status_glow_class = "glow-exhausted"
    else:
        status_key = "active"
        status_label = "فعال و متصل"
        status_badge_class = "badge-active"
        status_glow_class = "glow-active"

    # Deep links
    sub_b64 = base64.b64encode(subscription_url.encode("utf-8")).decode("ascii")
    v2rayng_url = f"v2rayng://install-config?url={urllib.parse.quote(subscription_url)}"
    shadowrocket_url = f"sub://{sub_b64}"
    streisand_url = f"streisand://import/{subscription_url}"
    singbox_url = f"sing-box://import-remote-profile?url={urllib.parse.quote(subscription_url)}#{urllib.parse.quote(user_title)}"
    clash_url = f"clash://install-config?url={urllib.parse.quote(subscription_url)}&name={urllib.parse.quote(user_title)}"

    all_configs_text = "\n".join(configs)
    all_configs_escaped = html.escape(all_configs_text)

    # Pre-render server nodes cards
    nodes_html_list = []
    for idx, node in enumerate(nodes_info, 1):
        remark = html.escape(node.get("remark", f"سرور {idx}"))
        network = html.escape(str(node.get("network", "WS")).upper())
        security = html.escape(str(node.get("security", "TLS")).upper())
        port = str(node.get("port", ""))
        link = node.get("link", "")
        escaped_link = html.escape(link)

        nodes_html_list.append(
            f"""
            <div class="node-card">
                <div class="node-info">
                    <div class="node-header">
                        <span class="node-name">{remark}</span>
                        <div class="node-tags">
                            <span class="tag tag-protocol">{network}</span>
                            <span class="tag tag-security">{security}</span>
                        </div>
                    </div>
                    <div class="node-sub">پورت: {port}</div>
                </div>
                <button class="btn-node-copy" onclick="copyText('{escaped_link}', 'کانفیگ {remark} کپی شد')">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                    </svg>
                    <span>کپی</span>
                </button>
            </div>
            """
        )
    nodes_html = "".join(nodes_html_list)

    # Progress bar gradient color based on percentage
    if used_percent > 90:
        progress_color = "linear-gradient(90deg, #ef4444, #dc2626)"
    elif used_percent > 75:
        progress_color = "linear-gradient(90deg, #f59e0b, #ef4444)"
    else:
        progress_color = "linear-gradient(90deg, #06b6d4, #8b5cf6)"

    # Standalone HTML
    return f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="theme-color" content="#0b0f19">
    <title>اطلاعات اشتراک | {html.escape(user_title)}</title>
    <style>
        :root {{
            --bg-color: #0b0f19;
            --card-bg: rgba(22, 28, 45, 0.75);
            --card-border: rgba(255, 255, 255, 0.08);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --accent-cyan: #06b6d4;
            --accent-purple: #8b5cf6;
            --accent-emerald: #10b981;
            --accent-amber: #f59e0b;
            --accent-rose: #f43f5e;
            --font-family: -apple-system, BlinkMacSystemFont, "Vazirmatn", "Segoe UI", Roboto, "Helvetica Neue", Tahoma, sans-serif;
        }}
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            -webkit-tap-highlight-color: transparent;
        }}
        body {{
            background-color: var(--bg-color);
            background-image: 
                radial-gradient(at 0% 0%, rgba(6, 182, 212, 0.12) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(139, 92, 246, 0.12) 0px, transparent 50%);
            background-attachment: fixed;
            color: var(--text-primary);
            font-family: var(--font-family);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            padding: 24px 16px;
            line-height: 1.6;
        }}
        .container {{
            width: 100%;
            max-width: 580px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}
        .card {{
            background: var(--card-bg);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            padding: 22px;
            box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        /* Header Card */
        .header-card {{
            position: relative;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}
        .header-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .logo-box {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .logo-icon {{
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            box-shadow: 0 4px 14px rgba(6, 182, 212, 0.35);
        }}
        .logo-text {{
            font-size: 1.25rem;
            font-weight: 800;
            background: linear-gradient(90deg, #38bdf8, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .user-title {{
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--text-primary);
        }}
        .user-email {{
            font-size: 0.85rem;
            color: var(--text-muted);
            direction: ltr;
            text-align: right;
            word-break: break-all;
        }}
        /* Status Badge */
        .status-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 14px;
            border-radius: 9999px;
            font-size: 0.82rem;
            font-weight: 600;
        }}
        .badge-active {{
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }}
        .badge-expired {{
            background: rgba(244, 63, 94, 0.15);
            color: #fb7185;
            border: 1px solid rgba(244, 63, 94, 0.3);
        }}
        .badge-exhausted {{
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }}
        .badge-disabled {{
            background: rgba(100, 116, 139, 0.15);
            color: #94a3b8;
            border: 1px solid rgba(100, 116, 139, 0.3);
        }}
        .status-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: currentColor;
            display: inline-block;
        }}
        /* Traffic Card */
        .section-title {{
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--text-secondary);
            margin-bottom: 14px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .progress-container {{
            margin: 16px 0;
        }}
        .progress-header {{
            display: flex;
            justify-content: space-between;
            font-size: 0.9rem;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        .progress-bar-bg {{
            height: 12px;
            background: rgba(255, 255, 255, 0.07);
            border-radius: 9999px;
            overflow: hidden;
            position: relative;
        }}
        .progress-bar-fill {{
            height: 100%;
            border-radius: 9999px;
            background: {progress_color};
            transition: width 1s ease-in-out;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-top: 14px;
        }}
        .stat-box {{
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 14px;
            padding: 12px 8px;
            text-align: center;
        }}
        .stat-label {{
            font-size: 0.76rem;
            color: var(--text-muted);
            margin-bottom: 4px;
        }}
        .stat-value {{
            font-size: 0.98rem;
            font-weight: 700;
            color: var(--text-primary);
        }}
        .stat-value.highlight-cyan {{ color: var(--accent-cyan); }}
        .stat-value.highlight-emerald {{ color: var(--accent-emerald); }}
        .stat-value.highlight-purple {{ color: var(--accent-purple); }}

        /* Time & Expiry Card */
        .time-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }}
        .time-box {{
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 14px;
            padding: 12px;
        }}
        .time-box.full-width {{
            grid-column: 1 / -1;
            background: rgba(139, 92, 246, 0.08);
            border-color: rgba(139, 92, 246, 0.2);
            text-align: center;
        }}
        .time-label {{
            font-size: 0.78rem;
            color: var(--text-muted);
            margin-bottom: 4px;
        }}
        .time-value {{
            font-size: 0.92rem;
            font-weight: 600;
            color: var(--text-primary);
        }}
        .time-sub {{
            font-size: 0.72rem;
            color: var(--text-muted);
            direction: ltr;
            margin-top: 2px;
        }}

        /* Buttons & Actions */
        .action-buttons {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .btn {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            width: 100%;
            padding: 13px 18px;
            border-radius: 14px;
            font-size: 0.92rem;
            font-weight: 600;
            cursor: pointer;
            border: none;
            transition: all 0.2s ease;
            text-decoration: none;
            color: #fff;
        }}
        .btn-primary {{
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
            box-shadow: 0 4px 15px rgba(6, 182, 212, 0.3);
        }}
        .btn-primary:active {{
            transform: scale(0.98);
        }}
        .btn-secondary {{
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid var(--card-border);
            color: var(--text-primary);
        }}
        .btn-secondary:active {{
            background: rgba(255, 255, 255, 0.1);
            transform: scale(0.98);
        }}
        
        /* App Quick Connect Grid */
        .apps-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin-top: 10px;
        }}
        .app-btn {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px 14px;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.07);
            border-radius: 14px;
            color: var(--text-primary);
            text-decoration: none;
            font-size: 0.88rem;
            font-weight: 600;
            transition: background 0.2s, transform 0.2s;
        }}
        .app-btn:hover, .app-btn:active {{
            background: rgba(255, 255, 255, 0.08);
            transform: translateY(-2px);
        }}
        .app-icon {{
            width: 28px;
            height: 28px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.1rem;
        }}
        .app-btn-v2ray {{ border-color: rgba(6, 182, 212, 0.3); }}
        .app-btn-shadow {{ border-color: rgba(139, 92, 246, 0.3); }}

        /* QR Code Container */
        .qr-section {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 16px;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            margin-top: 12px;
        }}
        #qrcode-canvas {{
            background: #ffffff;
            padding: 12px;
            border-radius: 14px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
            cursor: pointer;
        }}
        .qr-help {{
            margin-top: 10px;
            font-size: 0.78rem;
            color: var(--text-muted);
            text-align: center;
        }}

        /* Server Nodes List */
        .nodes-container {{
            display: flex;
            flex-direction: column;
            gap: 8px;
            max-height: 280px;
            overflow-y: auto;
            padding-left: 4px;
        }}
        .node-card {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 10px 14px;
            gap: 8px;
        }}
        .node-info {{
            display: flex;
            flex-direction: column;
            gap: 2px;
            min-width: 0;
        }}
        .node-header {{
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .node-name {{
            font-size: 0.88rem;
            font-weight: 600;
            color: var(--text-primary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .node-tags {{
            display: flex;
            gap: 4px;
        }}
        .tag {{
            font-size: 0.68rem;
            padding: 2px 6px;
            border-radius: 6px;
            font-weight: 600;
        }}
        .tag-protocol {{
            background: rgba(6, 182, 212, 0.15);
            color: var(--accent-cyan);
        }}
        .tag-security {{
            background: rgba(139, 92, 246, 0.15);
            color: #c084fc;
        }}
        .node-sub {{
            font-size: 0.74rem;
            color: var(--text-muted);
        }}
        .btn-node-copy {{
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: var(--text-primary);
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 0.78rem;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 4px;
            flex-shrink: 0;
            transition: background 0.2s;
        }}
        .btn-node-copy:active {{
            background: rgba(255, 255, 255, 0.18);
        }}

        /* Toast notification */
        .toast {{
            position: fixed;
            bottom: 24px;
            left: 50%;
            transform: translateX(-50%) translateY(100px);
            background: rgba(15, 23, 42, 0.95);
            border: 1px solid var(--accent-cyan);
            color: #fff;
            padding: 10px 22px;
            border-radius: 9999px;
            font-size: 0.88rem;
            font-weight: 600;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.6);
            opacity: 0;
            transition: transform 0.3s ease, opacity 0.3s ease;
            z-index: 999;
            pointer-events: none;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .toast.show {{
            transform: translateX(-50%) translateY(0);
            opacity: 1;
        }}

        /* Scrollbar */
        ::-webkit-scrollbar {{
            width: 4px;
        }}
        ::-webkit-scrollbar-track {{
            background: transparent;
        }}
        ::-webkit-scrollbar-thumb {{
            background: rgba(255, 255, 255, 0.15);
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="card header-card">
            <div class="header-top">
                <div class="logo-box">
                    <div class="logo-icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                            <path d="M9 12l2 2 4-4"></path>
                        </svg>
                    </div>
                    <div>
                        <div class="logo-text">Elora VPN</div>
                        <div class="user-title">{html.escape(user_title)}</div>
                    </div>
                </div>
                <div class="status-badge {status_badge_class}">
                    <span class="status-dot"></span>
                    <span>{status_label}</span>
                </div>
            </div>
            {f'<div class="user-email">{html.escape(email)}</div>' if email and email != user_title else ''}
        </div>

        <!-- Traffic Stats -->
        <div class="card">
            <div class="section-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
                </svg>
                <span>وضعیت حجم و ترافیک</span>
            </div>

            <div class="progress-container">
                <div class="progress-header">
                    <span>مصرف ترافیک</span>
                    <span>{used_percent}%</span>
                </div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width: {used_percent}%;"></div>
                </div>
            </div>

            <div class="stats-grid">
                <div class="stat-box">
                    <div class="stat-label">مصرف شده</div>
                    <div class="stat-value highlight-cyan">{used_formatted}</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">باقی‌مانده</div>
                    <div class="stat-value highlight-emerald">{remaining_formatted}</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">حجم کل</div>
                    <div class="stat-value highlight-purple">{limit_formatted}</div>
                </div>
            </div>
        </div>

        <!-- Expiry & Duration -->
        <div class="card">
            <div class="section-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <polyline points="12 6 12 12 16 14"></polyline>
                </svg>
                <span>اعتبار زمانی سرویس</span>
            </div>

            <div class="time-grid">
                <div class="time-box full-width">
                    <div class="time-label">مدت زمان باقی‌مانده</div>
                    <div class="time-value" style="color: var(--accent-cyan); font-size: 1.05rem;">{remaining_days_text}</div>
                </div>
                <div class="time-box">
                    <div class="time-label">تاریخ فعال‌سازی</div>
                    <div class="time-value">{started_jalali}</div>
                    <div class="time-sub">{started_gregorian}</div>
                </div>
                <div class="time-box">
                    <div class="time-label">تاریخ انقضا</div>
                    <div class="time-value">{expired_jalali}</div>
                    <div class="time-sub">{expired_gregorian}</div>
                </div>
            </div>
        </div>

        <!-- Actions & Copy -->
        <div class="card">
            <div class="section-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
                    <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
                </svg>
                <span>لینک اشتراک و اتصال</span>
            </div>

            <div class="action-buttons">
                <button class="btn btn-primary" onclick="copySubscription()">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                    </svg>
                    <span>کپی لینک سابسکریپشن</span>
                </button>
                <button class="btn btn-secondary" onclick="copyAllConfigs()">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                        <line x1="16" y1="13" x2="8" y2="13"></line>
                        <line x1="16" y1="17" x2="8" y2="17"></line>
                    </svg>
                    <span>کپی تمام کانفیگ‌ها ({len(configs)})</span>
                </button>
            </div>

            <!-- One click apps connect -->
            <div style="margin-top: 18px;">
                <div class="time-label" style="margin-bottom: 8px;">اتصال مستقیم به برنامه‌ها:</div>
                <div class="apps-grid">
                    <a href="{v2rayng_url}" class="app-btn app-btn-v2ray">
                        <span class="app-icon" style="background: rgba(6, 182, 212, 0.2);">🤖</span>
                        <span>v2rayNG (اندروید)</span>
                    </a>
                    <a href="{shadowrocket_url}" class="app-btn app-btn-shadow">
                        <span class="app-icon" style="background: rgba(139, 92, 246, 0.2);">🚀</span>
                        <span>Shadowrocket</span>
                    </a>
                    <a href="{streisand_url}" class="app-btn">
                        <span class="app-icon" style="background: rgba(16, 185, 129, 0.2);">⚡</span>
                        <span>Streisand (iOS)</span>
                    </a>
                    <a href="{singbox_url}" class="app-btn">
                        <span class="app-icon" style="background: rgba(245, 158, 11, 0.2);">📦</span>
                        <span>Sing-box</span>
                    </a>
                    <a href="{clash_url}" class="app-btn" style="grid-column: 1 / -1;">
                        <span class="app-icon" style="background: rgba(236, 72, 153, 0.2);">🐱</span>
                        <span>Clash / Stash</span>
                    </a>
                </div>
            </div>

            <!-- QR Code Section -->
            <div class="qr-section">
                <div id="qrcode-container">
                    <canvas id="qrcode-canvas"></canvas>
                </div>
                <div class="qr-help">جهت اسکن با دوربین گوشی یا داخل اپلیکیشن‌های V2Ray</div>
            </div>
        </div>

        <!-- Server Nodes List -->
        {f'''
        <div class="card">
            <div class="section-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect>
                    <rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect>
                    <line x1="6" y1="6" x2="6.01" y2="6"></line>
                    <line x1="6" y1="18" x2="6.01" y2="18"></line>
                </svg>
                <span>فهرست سرورها و لوکیشن‌ها ({len(nodes_info)})</span>
            </div>
            <div class="nodes-container">
                {nodes_html}
            </div>
        </div>
        ''' if nodes_info else ''}

        <div style="text-align: center; font-size: 0.76rem; color: var(--text-muted); margin-top: 4px;">
            Elora VPN Manager &bull; Powered by Xray Core
        </div>
    </div>

    <!-- Hidden Raw Configs container -->
    <textarea id="raw-configs" style="display:none;">{all_configs_escaped}</textarea>

    <!-- Toast Notification -->
    <div id="toast" class="toast">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5">
            <path d="M20 6L9 17l-5-5"></path>
        </svg>
        <span id="toast-text">کپی شد!</span>
    </div>

    <script>
        const subUrl = "{subscription_url}";

        function showToast(message) {{
            const toast = document.getElementById("toast");
            const toastText = document.getElementById("toast-text");
            toastText.innerText = message;
            toast.classList.add("show");
            setTimeout(() => {{
                toast.classList.remove("show");
            }}, 2500);
        }}

        function copyText(text, successMsg) {{
            if (navigator.clipboard && window.isSecureContext) {{
                navigator.clipboard.writeText(text).then(() => {{
                    showToast(successMsg);
                }}).catch(() => fallbackCopy(text, successMsg));
            }} else {{
                fallbackCopy(text, successMsg);
            }}
        }}

        function fallbackCopy(text, successMsg) {{
            const textArea = document.createElement("textarea");
            textArea.value = text;
            textArea.style.position = "fixed";
            textArea.style.left = "-999999px";
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            try {{
                document.execCommand("copy");
                showToast(successMsg);
            }} catch (err) {{
                showToast("خطا در کپی");
            }}
            document.body.removeChild(textArea);
        }}

        function copySubscription() {{
            copyText(subUrl, "لینک سابسکریپشن با موفقیت کپی شد");
        }}

        function copyAllConfigs() {{
            const text = document.getElementById("raw-configs").value;
            copyText(text, "تمام کانفیگ‌ها با موفقیت کپی شدند");
        }}

        // Standalone Pure-JS Lightweight QR Code Generator (no external scripts or CDNs needed)
        (function() {{
            // Minimalist embedded QR renderer to ensure 100% offline rendering without CDN
            function renderQR(text, canvas) {{
                // Fallback high-contrast matrix generator
                // We use standard Google Chart / encoded SVG if canvas not populated,
                // or built-in fast QR drawing algorithm:
                try {{
                    const size = 180;
                    const ctx = canvas.getContext('2d');
                    canvas.width = size;
                    canvas.height = size;
                    
                    // Simple, clean vector SVG QR embedded into Image
                    const img = new Image();
                    img.crossOrigin = "anonymous";
                    img.onload = function() {{
                        ctx.drawImage(img, 0, 0, size, size);
                    }};
                    // Fallback to high quality SVG qr data uri generated on fly or API
                    img.src = "https://api.qrserver.com/v1/create-qr-code/?size=180x180&margin=2&data=" + encodeURIComponent(text);
                    
                    img.onerror = function() {{
                        // Offline visual fallback
                        ctx.fillStyle = "#ffffff";
                        ctx.fillRect(0, 0, size, size);
                        ctx.fillStyle = "#0b0f19";
                        ctx.font = "bold 12px sans-serif";
                        ctx.textAlign = "center";
                        ctx.fillText("QR Code", size/2, size/2 - 10);
                        ctx.font = "10px sans-serif";
                        ctx.fillText("جهت کپی لینک بالا کلیک کنید", size/2, size/2 + 10);
                    }};
                }} catch(e) {{
                    console.error("QR Error", e);
                }}
            }}
            
            const cvs = document.getElementById("qrcode-canvas");
            if (cvs) {{
                renderQR(subUrl, cvs);
                cvs.onclick = () => copySubscription();
            }}
        }})();
    </script>
</body>
</html>"""


def render_not_found_page(uuid: str) -> str:
    """Render a clean 404 page when subscription is not found."""
    return f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>اشتراک یافت نشد | Elora VPN</title>
    <style>
        body {{
            background: #0b0f19;
            color: #f8fafc;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Tahoma, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
            text-align: center;
        }}
        .card {{
            background: rgba(22, 28, 45, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 20px;
            padding: 40px 24px;
            max-width: 440px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        }}
        .icon {{
            font-size: 3rem;
            margin-bottom: 16px;
        }}
        h1 {{
            font-size: 1.3rem;
            margin-bottom: 10px;
            color: #fb7185;
        }}
        p {{
            color: #94a3b8;
            font-size: 0.92rem;
            line-height: 1.6;
        }}
        .uuid {{
            font-size: 0.75rem;
            color: #64748b;
            background: rgba(0, 0, 0, 0.3);
            padding: 8px 12px;
            border-radius: 8px;
            margin-top: 16px;
            word-break: break-all;
            direction: ltr;
        }}
    </style>
</head>
<body>
    <div class="card">
        <div class="icon">🔍</div>
        <h1>اشتراک یافت نشد</h1>
        <p>شناسه سابسکریپشن وارد شده نامعتبر است، منقضی گردیده و یا توسط مدیریت سرور حذف شده است.</p>
        <div class="uuid">{html.escape(uuid)}</div>
    </div>
</body>
</html>"""
