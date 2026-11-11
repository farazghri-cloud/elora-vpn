import base64
import html
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
    """Renders a responsive, sleek, clean HTML dashboard for BESTPRIME V2RAY."""
    now = datetime.utcnow()

    # User & Title
    user_title = (
        account.user_title or account.service_title or account.email or "کاربر گرامی"
    )
    email = account.email or ""

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
                remaining_days_text = f"{days} روز و {hours} ساعت باقی‌مانده"
            else:
                remaining_days_text = f"{hours} ساعت باقی‌مانده"
    else:
        remaining_days_text = "نامحدود (بدون انقضا)"

    expired_jalali = format_jalali_date(expired_at)

    # Status detection
    if not account.enable:
        status_label = "غیرفعال شده"
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

    # Pre-render server nodes cards (read-only list, non-copyable)
    nodes_html_list = []
    for idx, node in enumerate(nodes_info, 1):
        remark = html.escape(node.get("remark", f"سرور {idx}"))
        network = html.escape(str(node.get("network", "WS")).upper())
        security = html.escape(str(node.get("security", "TLS")).upper())
        port = str(node.get("port", ""))

        nodes_html_list.append(
            f'''
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
            '''
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
    return f'''<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="theme-color" content="#0b0f19">
    <title>BESTPRIME V2RAY | {html.escape(user_title)}</title>
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
        
        /* Header Card with Expiry Integration */
        .header-card {{
            display: flex;
            flex-direction: column;
            gap: 14px;
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
            background: linear-gradient(135deg, #2563eb, #7c3aed);
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4);
        }}
        .brand-title {{
            font-size: 1.15rem;
            font-weight: 900;
            letter-spacing: 0.5px;
            background: linear-gradient(90deg, #38bdf8, #a855f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .user-title {{
            font-size: 0.92rem;
            font-weight: 700;
            color: var(--text-primary);
        }}
        
        .header-actions {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        /* Telegram Support Button */
        .btn-telegram {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 36px;
            height: 36px;
            background: rgba(34, 158, 217, 0.15);
            border: 1px solid rgba(34, 158, 217, 0.35);
            border-radius: 10px;
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
            padding: 5px 12px;
            border-radius: 9999px;
            font-size: 0.8rem;
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
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background-color: currentColor;
            display: inline-block;
        }}

        /* Combined Expiry Banner in Header */
        .expiry-banner {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 12px;
            padding: 10px 14px;
            font-size: 0.82rem;
        }}
        .expiry-days {{
            font-weight: 700;
            color: var(--accent-cyan);
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .expiry-date {{
            color: var(--text-muted);
            direction: ltr;
        }}

        /* Traffic Card */
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
            margin: 12px 0 16px 0;
        }}
        .progress-header {{
            display: flex;
            justify-content: space-between;
            font-size: 0.88rem;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        .progress-bar-bg {{
            height: 10px;
            background: rgba(255, 255, 255, 0.07);
            border-radius: 9999px;
            overflow: hidden;
        }}
        .progress-bar-fill {{
            height: 100%;
            border-radius: 9999px;
            background: {progress_color};
            transition: width 0.8s ease-in-out;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
        }}
        .stat-box {{
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 10px 6px;
            text-align: center;
        }}
        .stat-label {{
            font-size: 0.74rem;
            color: var(--text-muted);
            margin-bottom: 4px;
        }}
        .stat-value {{
            font-size: 0.92rem;
            font-weight: 700;
            color: var(--text-primary);
        }}
        .stat-value.highlight-cyan {{ color: var(--accent-cyan); }}
        .stat-value.highlight-emerald {{ color: var(--accent-emerald); }}
        .stat-value.highlight-purple {{ color: var(--accent-purple); }}

        /* Subscription & QR Card */
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

        /* Server Locations List (Non-copyable, informational only) */
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
        <!-- Header & Expiry Info Combined -->
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
                        <div class="brand-title">BESTPRIME V2RAY</div>
                        <div class="user-title">{html.escape(user_title)}</div>
                    </div>
                </div>
                
                <div class="header-actions">
                    <!-- Telegram Support Link -->
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

            <!-- Integrated Expiry Banner -->
            <div class="expiry-banner">
                <div class="expiry-days">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <polyline points="12 6 12 12 16 14"></polyline>
                    </svg>
                    <span>{remaining_days_text}</span>
                </div>
                <div class="expiry-date">انقضا: {expired_jalali}</div>
            </div>
        </div>

        <!-- Traffic Stats -->
        <div class="card">
            <div class="section-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
                </svg>
                <span>وضعیت حجم و مصرف</span>
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

            <!-- QR Code Section -->
            <div class="qr-section">
                <div id="qrcode-container">
                    <canvas id="qrcode-canvas"></canvas>
                </div>
                <div class="qr-help">اسکن با دوربین یا نرم‌افزارهای V2Ray جهت اتصال سریع</div>
            </div>
        </div>

        <!-- Server Locations List (Informational Only) -->
        {f'''
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
        ''' if nodes_info else ''}

        <div style="text-align: center; font-size: 0.74rem; color: var(--text-muted); margin-top: 2px;">
            BESTPRIME V2RAY &bull; طراحی شده برای اتصال پرسرعت و پایدار
        </div>
    </div>

    <!-- Toast Notification -->
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

        // QR Code Generator
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
</html>'''


def render_not_found_page(uuid: str) -> str:
    """Render a clean 404 page when subscription is not found."""
    return f'''<!DOCTYPE html>
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
</html>'''
