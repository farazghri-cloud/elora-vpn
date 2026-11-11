import base64
import datetime
import io
from typing import Optional, Tuple


def gregorian_to_jalali(gy: int, gm: int, gd: int) -> Tuple[int, int, int]:
    """Pure-Python Gregorian to Jalali date converter (zero external dependencies)."""
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    if gy > 1600:
        jy = 979
        gy -= 1600
    else:
        jy = 0
        gy -= 621
    gy2 = gy + 1 if gm > 2 else gy
    days = (
        (365 * gy)
        + ((gy2 + 3) // 4)
        - ((gy2 + 99) // 100)
        + ((gy2 + 399) // 400)
        - 80
        + gd
        + g_d_m[gm - 1]
    )
    jy += 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + (days // 31)
        jd = 1 + (days % 31)
    else:
        jm = 7 + ((days - 186) // 30)
        jd = 1 + ((days - 186) % 30)
    return jy, jm, jd


def format_bytes(num_bytes: Optional[int]) -> str:
    """Format bytes to human readable string (B, KB, MB, GB, TB)."""
    if num_bytes is None or num_bytes < 0:
        return "0 B"
    if num_bytes < 1024:
        return f"{num_bytes} B"
    elif num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    elif num_bytes < 1024 * 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.2f} MB"
    elif num_bytes < 1024 * 1024 * 1024 * 1024:
        return f"{num_bytes / (1024 * 1024 * 1024):.2f} GB"
    else:
        return f"{num_bytes / (1024 * 1024 * 1024 * 1024):.2f} TB"


def format_jalali_date(dt: Optional[datetime.datetime]) -> str:
    """Format datetime into Jalali string (YYYY/MM/DD - HH:MM)."""
    if not dt:
        return "ثبت نشده"
    jy, jm, jd = gregorian_to_jalali(dt.year, dt.month, dt.day)
    return f"{jy:04d}/{jm:02d}/{jd:02d} - {dt.hour:02d}:{dt.minute:02d}"


def format_gregorian_date(dt: Optional[datetime.datetime]) -> str:
    """Format datetime into Gregorian string (YYYY-MM-DD HH:MM)."""
    if not dt:
        return "-"
    return dt.strftime("%Y-%m-%d %H:%M")


def generate_qr_data_uri(data: str) -> Optional[str]:
    """Generate a base64 PNG/SVG QR Code data URI offline if qrcode or pyqrcode is available."""
    import importlib
    try:
        qrcode_mod = importlib.import_module("qrcode")
        qr = qrcode_mod.QRCode(version=1, box_size=6, border=2)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/png;base64,{b64}"
    except Exception:
        pass

    try:
        pyqrcode_mod = importlib.import_module("pyqrcode")
        qr = pyqrcode_mod.create(data)
        buf = io.BytesIO()
        qr.svg(buf, scale=5, background="white", module_color="#000000")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/svg+xml;base64,{b64}"
    except Exception:
        return None
