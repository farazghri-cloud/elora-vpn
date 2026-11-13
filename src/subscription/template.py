import base64
import html
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.subscription.utils import (
    format_bytes,
    format_gregorian_date,
    format_jalali_date,
)

BRAND_LOGO_DATA_URI = "data:image/jpeg;base64,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"


def render_subscription_page(
    account: Any,
    configs: List[str],
    nodes_info: List[Dict[str, Any]],
    subscription_url: str,
) -> str:
    now = datetime.utcnow()

    user_title = (
        account.user_title or account.service_title or account.email or "کاربر گرامی"
    )
    email = account.email or ""

    used_bytes = int(account.used_traffic or 0)
    limit_bytes = int(account.data_limit or 0)
    is_unlimited_traffic = limit_bytes <= 0

    if is_unlimited_traffic:
        remaining_bytes = 0
        used_percent_str = "0"
        bar_width = 0.0
        used_formatted = format_bytes(used_bytes)
        remaining_formatted = "نامحدود"
        limit_formatted = "نامحدود"
    else:
        remaining_bytes = max(0, limit_bytes - used_bytes)
        if limit_bytes > 0:
            raw_pct = (used_bytes / limit_bytes) * 100.0
            if used_bytes > 0 and raw_pct < 0.1:
                used_percent_str = f"{raw_pct:.2f}"
                bar_width = max(2.5, raw_pct)
            elif used_bytes > 0:
                used_percent_str = f"{min(100.0, raw_pct):.1f}"
                bar_width = max(2.0, min(100.0, raw_pct))
            else:
                used_percent_str = "0"
                bar_width = 0.0
        else:
            used_percent_str = "0"
            bar_width = 0.0
        used_formatted = format_bytes(used_bytes)
        remaining_formatted = format_bytes(remaining_bytes)
        limit_formatted = format_bytes(limit_bytes)

    is_expired = False
    remaining_days_text = ""
    expired_at = account.expired_at

    if expired_at:
        delta = expired_at - now
        if delta.total_seconds() <= 0:
            is_expired = True
            remaining_days_text = "منقضی شده"
            expiry_date_display = "منقضی شده"
        elif delta.days > 365:
            remaining_days_text = "نامحدود"
            expiry_date_display = "نامحدود"
        else:
            days = delta.days
            hours = int(delta.seconds // 3600)
            if days > 0:
                remaining_days_text = f"{days} روز و {hours} ساعت"
            else:
                remaining_days_text = f"{hours} ساعت"
            expiry_date_display = format_jalali_date(expired_at)
    else:
        remaining_days_text = "نامحدود"
        expiry_date_display = "نامحدود"

    if not account.enable:
        status_label = "غیرفعال"
        status_badge_class = "badge-disabled"
    elif is_expired:
        status_label = "منقضی شده"
        status_badge_class = "badge-expired"
    elif not is_unlimited_traffic and used_bytes >= limit_bytes:
        status_label = "اتمام حجم"
        status_badge_class = "badge-exhausted"
    else:
        status_label = "فعال و متصل"
        status_badge_class = "badge-active"

    nodes_html_list = []
    for idx, node in enumerate(nodes_info, 1):
        remark = html.escape(node.get("remark", f"سرور {idx}"))
        network = html.escape(str(node.get("network", "WS")).upper())
        security = html.escape(str(node.get("security", "TLS")).upper())
        port = str(node.get("port", ""))

        nodes_html_list.append(
            f"""
            <div class="node-card">
                <div class="node-info">
                    <div class="node-header">
                        <span class="node-dot"></span>
                        <span class="node-name">{remark}</span>
                    </div>
                    <div class="node-sub">پورت: {port}</div>
                </div>
                <div class="node-tags">
                    <span class="tag tag-protocol">{network}</span>
                    <span class="tag tag-security">{security}</span>
                </div>
            </div>
            """
        )
    nodes_html = "".join(nodes_html_list)

    if bar_width > 90:
        progress_color = "linear-gradient(90deg, #ef4444, #dc2626)"
    elif bar_width > 75:
        progress_color = "linear-gradient(90deg, #f59e0b, #ef4444)"
    else:
        progress_color = "linear-gradient(90deg, #06b6d4, #8b5cf6)"

    locations_section = ""
    if nodes_info:
        locations_section = f"""
        <div class="card">
            <div class="section-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect>
                    <rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect>
                    <line x1="6" y1="6" x2="6.01" y2="6"></line>
                    <line x1="6" y1="18" x2="6.01" y2="18"></line>
                </svg>
                <span>لوکیشن‌های فعال در این اشتراک ({len(nodes_info)})</span>
            </div>
            <div class="nodes-container">
                {nodes_html}
            </div>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="theme-color" content="#0b0f19">
    <link rel="icon" type="image/jpeg" href="{BRAND_LOGO_DATA_URI}">
    <title>BESTPRIME V2RAY | {html.escape(user_title)}</title>
    <style>
        :root {{
            --bg-color: #0b0f19;
            --card-bg: rgba(22, 28, 45, 0.78);
            --card-border: rgba(255, 255, 255, 0.08);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --accent-cyan: #06b6d4;
            --accent-purple: #8b5cf6;
            --accent-emerald: #10b981;
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
            padding: 20px 16px;
            line-height: 1.6;
        }}
        .container {{
            width: 100%;
            max-width: 520px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}
        .card {{
            background: var(--card-bg);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
        }}
        .header-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .logo-box {{
            display: flex;
            align-items: center;
            gap: 14px;
        }}
        .logo-img {{
            width: 48px;
            height: 48px;
            border-radius: 14px;
            object-fit: cover;
            border: 2px solid rgba(6, 182, 212, 0.4);
            box-shadow: 0 4px 15px rgba(6, 182, 212, 0.25);
        }}
        .brand-title {{
            font-size: 1.15rem;
            font-weight: 900;
            letter-spacing: 0.5px;
            background: linear-gradient(90deg, #38bdf8, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .user-title {{
            font-size: 0.9rem;
            font-weight: 700;
            color: var(--text-primary);
        }}
        .header-actions {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .btn-telegram {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 38px;
            height: 38px;
            background: rgba(34, 158, 217, 0.15);
            border: 1px solid rgba(34, 158, 217, 0.35);
            border-radius: 11px;
            color: #38bdf8;
            text-decoration: none;
            transition: all 0.2s;
        }}
        .btn-telegram:hover, .btn-telegram:active {{
            background: #229ED9;
            color: #fff;
            transform: scale(1.05);
        }}
        .status-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            border-radius: 9999px;
            font-size: 0.78rem;
            font-weight: 700;
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
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background-color: currentColor;
            display: inline-block;
        }}
        .section-title {{
            font-size: 0.92rem;
            font-weight: 700;
            color: var(--text-secondary);
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .progress-container {{
            margin: 10px 0 16px 0;
        }}
        .progress-header {{
            display: flex;
            justify-content: space-between;
            font-size: 0.86rem;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        .progress-bar-bg {{
            height: 10px;
            background: rgba(255, 255, 255, 0.07);
            border-radius: 9999px;
            overflow: hidden;
            display: flex;
            justify-content: flex-start;
        }}
        .progress-bar-fill {{
            height: 100%;
            border-radius: 9999px;
            background: {progress_color};
            box-shadow: 0 0 10px rgba(6, 182, 212, 0.6);
            transition: width 0.8s ease-in-out;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }}
        .metric-box {{
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 14px;
            padding: 12px 14px;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .metric-icon {{
            width: 36px;
            height: 36px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }}
        .icon-cyan {{
            background: rgba(6, 182, 212, 0.15);
            color: var(--accent-cyan);
        }}
        .icon-emerald {{
            background: rgba(16, 185, 129, 0.15);
            color: var(--accent-emerald);
        }}
        .icon-purple {{
            background: rgba(139, 92, 246, 0.15);
            color: #c084fc;
        }}
        .icon-amber {{
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
        }}
        .metric-content {{
            display: flex;
            flex-direction: column;
            min-width: 0;
        }}
        .metric-label {{
            font-size: 0.74rem;
            color: var(--text-muted);
            margin-bottom: 2px;
        }}
        .metric-val {{
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--text-primary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
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
            font-weight: 700;
            cursor: pointer;
            border: none;
            transition: all 0.2s ease;
            color: #fff;
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
            box-shadow: 0 4px 15px rgba(6, 182, 212, 0.3);
        }}
        .btn:active {{
            transform: scale(0.98);
        }}
        .qr-section {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 16px;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            margin-top: 14px;
        }}
        #qrcode-canvas {{
            background: #ffffff;
            padding: 10px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
            cursor: pointer;
        }}
        .qr-help {{
            margin-top: 8px;
            font-size: 0.76rem;
            color: var(--text-muted);
            text-align: center;
        }}
        .nodes-container {{
            display: flex;
            flex-direction: column;
            gap: 8px;
            max-height: 240px;
            overflow-y: auto;
            padding-left: 2px;
        }}
        .node-card {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 10px 14px;
            user-select: none;
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
        }}
        .node-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: var(--accent-emerald);
            flex-shrink: 0;
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
            flex-shrink: 0;
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
            padding-right: 16px;
        }}
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
        <div class="card">
            <div class="header-top">
                <div class="logo-box">
                    <img src="{BRAND_LOGO_DATA_URI}" alt="BESTPRIME" class="logo-img">
                    <div>
                        <div class="brand-title">BESTPRIME V2RAY</div>
                        <div class="user-title">{html.escape(user_title)}</div>
                    </div>
                </div>
                
                <div class="header-actions">
                    <a href="https://t.me/acstoreir" target="_blank" rel="noopener noreferrer" class="btn-telegram" title="پشتیبانی تلگرام">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69.01-.03.01-.14-.07-.19-.08-.05-.19-.02-.27 0-.12.03-1.99 1.27-5.63 3.73-.53.36-1.02.54-1.45.53-.48-.01-1.4-.27-2.09-.49-.84-.27-1.51-.42-1.45-.89.03-.25.38-.51 1.07-.78 4.19-1.82 6.99-3.03 8.39-3.61 3.99-1.66 4.82-1.95 5.36-1.96.12 0 .38.03.55.17.14.12.18.28.2.4.01.07.02.21 0 .36z"/>
                        </svg>
                    </a>
                    
                    <div class="status-badge {status_badge_class}">
                        <span class="status-dot"></span>
                        <span>{status_label}</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Integrated Traffic & Validity Dashboard Card -->
        <div class="card">
            <div class="section-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
                </svg>
                <span>وضعیت مصرف و اعتبار سرویس</span>
            </div>

            <div class="progress-container">
                <div class="progress-header">
                    <span>مصرف ترافیک</span>
                    <span>{used_percent_str}%</span>
                </div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width: {bar_width}%;"></div>
                </div>
            </div>

            <div class="metrics-grid">
                <!-- Consumed Traffic -->
                <div class="metric-box">
                    <div class="metric-icon icon-cyan">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
                            <polyline points="17 6 23 6 23 12"></polyline>
                        </svg>
                    </div>
                    <div class="metric-content">
                        <span class="metric-label">مصرف شده</span>
                        <span class="metric-val" style="color: var(--accent-cyan);">{used_formatted}</span>
                    </div>
                </div>

                <!-- Remaining Traffic -->
                <div class="metric-box">
                    <div class="metric-icon icon-emerald">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
                        </svg>
                    </div>
                    <div class="metric-content">
                        <span class="metric-label">باقی‌مانده حجم</span>
                        <span class="metric-val" style="color: var(--accent-emerald);">{remaining_formatted}</span>
                    </div>
                </div>

                <!-- Total Quota -->
                <div class="metric-box">
                    <div class="metric-icon icon-purple">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect>
                            <rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect>
                        </svg>
                    </div>
                    <div class="metric-content">
                        <span class="metric-label">سقف کل حجم</span>
                        <span class="metric-val" style="color: #c084fc;">{limit_formatted}</span>
                    </div>
                </div>

                <!-- Remaining Validity Time -->
                <div class="metric-box">
                    <div class="metric-icon icon-amber">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"></circle>
                            <polyline points="12 6 12 12 16 14"></polyline>
                        </svg>
                    </div>
                    <div class="metric-content">
                        <span class="metric-label">زمان باقی‌مانده</span>
                        <span class="metric-val" style="color: #fbbf24;">{remaining_days_text}</span>
                    </div>
                </div>
            </div>
            
            <div style="margin-top: 14px; font-size: 0.78rem; color: var(--text-muted); display: flex; justify-content: space-between; align-items: center; padding: 0 4px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 10px;">
                <span>تاریخ انقضای اشتراک:</span>
                <span style="direction: ltr; font-weight: 600; color: var(--text-secondary);">{expiry_date_display}</span>
            </div>
        </div>

        <!-- Subscription Link & QR -->
        <div class="card">
            <div class="section-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
                    <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
                </svg>
                <span>لینک سابسکریپشن</span>
            </div>

            <button class="btn" onclick="copySubscription()">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                </svg>
                <span>کپی لینک سابسکریپشن</span>
            </button>

            <div class="qr-section">
                <div id="qrcode-container">
                    <canvas id="qrcode-canvas"></canvas>
                </div>
                <div class="qr-help">اسکن با دوربین گوشی یا نرم‌افزارهای V2Ray جهت اتصال</div>
            </div>
        </div>

        {locations_section}

        <div style="text-align: center; font-size: 0.74rem; color: var(--text-muted); margin-top: 2px;">
            BESTPRIME V2RAY &bull; طراحی شده برای اتصال پرسرعت و پایدار
        </div>
    </div>

    <div id="toast" class="toast">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5">
            <path d="M20 6L9 17l-5-5"></path>
        </svg>
        <span id="toast-text">لینک سابسکریپشن کپی شد</span>
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

        function copySubscription() {{
            if (navigator.clipboard && window.isSecureContext) {{
                navigator.clipboard.writeText(subUrl).then(() => {{
                    showToast("لینک سابسکریپشن با موفقیت کپی شد");
                }}).catch(() => fallbackCopy(subUrl));
            }} else {{
                fallbackCopy(subUrl);
            }}
        }}

        function fallbackCopy(text) {{
            const textArea = document.createElement("textarea");
            textArea.value = text;
            textArea.style.position = "fixed";
            textArea.style.left = "-999999px";
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            try {{
                document.execCommand("copy");
                showToast("لینک سابسکریپشن با موفقیت کپی شد");
            }} catch (err) {{
                showToast("خطا در کپی لینک");
            }}
            document.body.removeChild(textArea);
        }}

        (function() {{
            function renderQR(text, canvas) {{
                try {{
                    const size = 180;
                    const ctx = canvas.getContext('2d');
                    canvas.width = size;
                    canvas.height = size;
                    
                    const img = new Image();
                    img.crossOrigin = "anonymous";
                    img.onload = function() {{
                        ctx.drawImage(img, 0, 0, size, size);
                    }};
                    img.src = "https://api.qrserver.com/v1/create-qr-code/?size=180x180&margin=2&data=" + encodeURIComponent(text);
                    
                    img.onerror = function() {{
                        ctx.fillStyle = "#ffffff";
                        ctx.fillRect(0, 0, size, size);
                        ctx.fillStyle = "#0b0f19";
                        ctx.font = "bold 12px sans-serif";
                        ctx.textAlign = "center";
                        ctx.fillText("QR Code", size/2, size/2);
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
    return f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>اشتراک یافت نشد | BESTPRIME V2RAY</title>
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
        <p>شناسه سابسکریپشن وارد شده نامعتبر است، منقضی گردیده و یا توسط مدیریت حذف شده است.</p>
        <div class="uuid">{html.escape(uuid)}</div>
    </div>
</body>
</html>"""
