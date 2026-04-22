import calendar
import html
import os
import re
import secrets
import smtplib
import sqlite3
import urllib.parse
from datetime import date, datetime, timedelta
from email.message import EmailMessage
from hashlib import pbkdf2_hmac
from http import cookies
from http.server import BaseHTTPRequestHandler, HTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "salarycalc.db")
STATIC_DIR = os.path.join(BASE_DIR, "static")
HOST = "127.0.0.1"
PORT = 8080

SESSIONS = {}
INCOME_TAX_RATE = 0.1275
ACCOMMODATION_DEDUCTION_ILS = 500.0
TRANSPORT_ALLOWANCE_ILS = 315.0
OVERTIME_CFG = {"base_hours": 7.0, "base_percent": 100.0, "tier1_hours": 2.0, "tier1_percent": 125.0, "tier2_hours": 2.0, "tier2_percent": 150.0, "after_percent": 150.0}

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER or "no-reply@example.com")
LANGUAGE_OPTIONS = [("en", "English"), ("he", "Hebrew"), ("ru", "Russian"), ("ne", "Nepali")]
TRANSLATIONS = {
    "en": {
        "home": "Home", "dashboard": "Dashboard", "logout": "Logout", "login": "Login", "register": "Register",
        "welcome_back": "Welcome back", "create_account": "Create account", "full_name": "Full name", "email": "Email",
        "password": "Password", "forgot_password": "Forgot Password", "send_otp": "Send OTP", "verify_otp": "Verify OTP",
        "reset_password": "Reset Password", "new_password": "New Password", "confirm_password": "Confirm Password",
        "manual_salary_calendar": "Manual Salary Calendar", "open_calendar": "Open Calendar",
        "calendar_desc": "Track duty entries day-by-day, edit any date instantly, and get monthly net salary calculations.",
        "hello": "Hello", "work_calendar": "Work Calendar", "monthly_payroll": "Monthly Payroll", "day_editor": "Day Editor",
        "previous": "Previous", "next": "Next", "total_worked": "Total Worked", "total_break": "Total Break",
        "gross_salary": "Gross Salary", "income_tax": "Income Tax 12.75%", "accommodation": "Accommodation -500 ILS",
        "total_deductions": "Total Deductions", "after_deductions": "After Deductions", "transport": "Transport +315 ILS",
        "final_net": "Final Net Salary", "entries_for": "Entries for", "start": "Start", "end": "End", "notes": "Notes",
        "festival": "Festival", "actions": "Actions", "save": "Save", "delete": "Delete", "add_entry": "Add Entry",
        "base_rate": "Base Rate / Hour", "save_rate": "Save Rate", "from": "From", "to": "To", "rate_percent": "Rate %",
        "h125": "125% Hours", "h150": "150% Hours", "festival_hours": "Festival Hours",
        "festival_premium": "Festival Premium", "lang": "Language",
    },
    "he": {
        "home": "בית", "dashboard": "לוח בקרה", "logout": "התנתק", "login": "התחברות", "register": "הרשמה",
        "welcome_back": "ברוך שובך", "create_account": "יצירת חשבון", "full_name": "שם מלא", "email": "אימייל",
        "password": "סיסמה", "forgot_password": "שכחתי סיסמה", "send_otp": "שלח OTP", "verify_otp": "אימות OTP",
        "reset_password": "איפוס סיסמה", "new_password": "סיסמה חדשה", "confirm_password": "אימות סיסמה",
        "manual_salary_calendar": "לוח שכר ידני", "open_calendar": "פתח לוח שנה",
        "calendar_desc": "ניהול משמרות יומי, עריכה מהירה וחישוב שכר חודשי נטו.",
        "hello": "שלום", "work_calendar": "לוח עבודה", "monthly_payroll": "שכר חודשי", "day_editor": "עריכת יום",
        "previous": "קודם", "next": "הבא", "total_worked": "סה\"כ שעות", "total_break": "סה\"כ הפסקות",
        "gross_salary": "שכר ברוטו", "income_tax": "מס הכנסה 12.75%", "accommodation": "ניכוי מגורים 500-",
        "total_deductions": "סה\"כ ניכויים", "after_deductions": "אחרי ניכויים", "transport": "נסיעות +315",
        "final_net": "שכר נטו סופי", "entries_for": "רשומות עבור", "start": "התחלה", "end": "סיום", "notes": "הערות",
        "festival": "חג", "actions": "פעולות", "save": "שמירה", "delete": "מחיקה", "add_entry": "הוסף רשומה",
        "base_rate": "תעריף לשעה", "save_rate": "שמור תעריף", "from": "מ-", "to": "עד", "rate_percent": "% תעריף",
        "h125": "שעות 125%", "h150": "שעות 150%", "festival_hours": "שעות חג",
        "festival_premium": "תוספת חג", "lang": "שפה",
    },
    "ru": {
        "home": "Главная", "dashboard": "Панель", "logout": "Выйти", "login": "Вход", "register": "Регистрация",
        "welcome_back": "С возвращением", "create_account": "Создать аккаунт", "full_name": "Полное имя", "email": "Email",
        "password": "Пароль", "forgot_password": "Забыли пароль", "send_otp": "Отправить OTP", "verify_otp": "Проверить OTP",
        "reset_password": "Сброс пароля", "new_password": "Новый пароль", "confirm_password": "Подтвердите пароль",
        "manual_salary_calendar": "Календарь зарплаты", "open_calendar": "Открыть календарь",
        "calendar_desc": "Учет смен по дням, редактирование дат и расчет чистой зарплаты за месяц.",
        "hello": "Здравствуйте", "work_calendar": "Календарь работы", "monthly_payroll": "Зарплата за месяц", "day_editor": "Редактор дня",
        "previous": "Назад", "next": "Вперед", "total_worked": "Всего часов", "total_break": "Перерывы",
        "gross_salary": "Брутто", "income_tax": "Налог 12.75%", "accommodation": "Жилье -500 ILS",
        "total_deductions": "Всего удержаний", "after_deductions": "После удержаний", "transport": "Транспорт +315 ILS",
        "final_net": "Итоговая нетто", "entries_for": "Записи за", "start": "Начало", "end": "Конец", "notes": "Заметки",
        "festival": "Праздник", "actions": "Действия", "save": "Сохранить", "delete": "Удалить", "add_entry": "Добавить",
        "base_rate": "Ставка в час", "save_rate": "Сохранить ставку", "from": "С", "to": "До", "rate_percent": "Ставка %",
        "h125": "Часы 125%", "h150": "Часы 150%", "festival_hours": "Праздничные часы",
        "festival_premium": "Праздничная доплата", "lang": "Язык",
    },
    "ne": {
        "home": "होम", "dashboard": "ड्यासबोर्ड", "logout": "लगआउट", "login": "लगइन", "register": "दर्ता",
        "welcome_back": "फेरि स्वागत छ", "create_account": "खाता बनाउनुहोस्", "full_name": "पूरा नाम", "email": "इमेल",
        "password": "पासवर्ड", "forgot_password": "पासवर्ड बिर्सनुभयो", "send_otp": "OTP पठाउनुहोस्", "verify_otp": "OTP जाँच",
        "reset_password": "पासवर्ड रिसेट", "new_password": "नयाँ पासवर्ड", "confirm_password": "पासवर्ड पुष्टि",
        "manual_salary_calendar": "म्यानुअल तलब क्यालेन्डर", "open_calendar": "क्यालेन्डर खोल्नुहोस्",
        "calendar_desc": "दैनिक ड्युटी प्रविष्टि, मिति अनुसार सम्पादन र मासिक नेट तलब गणना।",
        "hello": "नमस्ते", "work_calendar": "काम क्यालेन्डर", "monthly_payroll": "मासिक तलब", "day_editor": "दैनिक सम्पादक",
        "previous": "अघिल्लो", "next": "अर्को", "total_worked": "कुल काम", "total_break": "कुल ब्रेक",
        "gross_salary": "ग्रस तलब", "income_tax": "आयकर 12.75%", "accommodation": "बसोबास कटौती -500 ILS",
        "total_deductions": "कुल कटौती", "after_deductions": "कटौतीपछि", "transport": "यातायात +315 ILS",
        "final_net": "अन्तिम नेट तलब", "entries_for": "यो मितिको प्रविष्टि", "start": "सुरु", "end": "अन्त्य", "notes": "टिप्पणी",
        "festival": "चाडपर्व", "actions": "कार्य", "save": "सेभ", "delete": "मेटाउनुहोस्", "add_entry": "प्रविष्टि थप्नुहोस्",
        "base_rate": "प्रति घण्टा दर", "save_rate": "दर सेभ", "from": "बाट", "to": "सम्म", "rate_percent": "दर %",
        "h125": "125% घण्टा", "h150": "150% घण्टा", "festival_hours": "चाडपर्व घण्टा",
        "festival_premium": "चाडपर्व अतिरिक्त", "lang": "भाषा",
    },
}


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            hourly_rate REAL NOT NULL DEFAULT 45,
            language TEXT NOT NULL DEFAULT 'en',
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS work_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            work_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            notes TEXT,
            hourly_rate REAL NOT NULL DEFAULT 45,
            festival_enabled INTEGER NOT NULL DEFAULT 0,
            festival_start_time TEXT,
            festival_end_time TEXT,
            festival_percent REAL NOT NULL DEFAULT 150,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS password_resets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            otp_code TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    user_cols = [r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "hourly_rate" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN hourly_rate REAL NOT NULL DEFAULT 45")
    if "language" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN language TEXT NOT NULL DEFAULT 'en'")
    entry_cols = [r[1] for r in conn.execute("PRAGMA table_info(work_entries)").fetchall()]
    if "festival_enabled" not in entry_cols:
        conn.execute("ALTER TABLE work_entries ADD COLUMN festival_enabled INTEGER NOT NULL DEFAULT 0")
    if "festival_start_time" not in entry_cols:
        conn.execute("ALTER TABLE work_entries ADD COLUMN festival_start_time TEXT")
    if "festival_end_time" not in entry_cols:
        conn.execute("ALTER TABLE work_entries ADD COLUMN festival_end_time TEXT")
    if "festival_percent" not in entry_cols:
        conn.execute("ALTER TABLE work_entries ADD COLUMN festival_percent REAL NOT NULL DEFAULT 150")
    conn.commit()
    conn.close()


def db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password):
    salt = secrets.token_bytes(16)
    key = pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 150_000)
    return f"{salt.hex()}:{key.hex()}"


def verify_password(password, stored):
    salt_hex, key_hex = stored.split(":")
    key = pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), 150_000)
    return key.hex() == key_hex


def month_bounds(month_str):
    try:
        y, m = month_str.split("-", 1)
        first = date(int(y), int(m), 1)
    except Exception:
        t = date.today()
        first = date(t.year, t.month, 1)
    _, last_day = calendar.monthrange(first.year, first.month)
    return first, date(first.year, first.month, last_day)


def prev_next_month(month_str):
    first, _ = month_bounds(month_str)
    prev_m = date(first.year - 1, 12, 1) if first.month == 1 else date(first.year, first.month - 1, 1)
    next_m = date(first.year + 1, 1, 1) if first.month == 12 else date(first.year, first.month + 1, 1)
    return prev_m.strftime("%Y-%m"), next_m.strftime("%Y-%m")


def time_to_minutes(v):
    if not v or not re.fullmatch(r"\d{1,2}:\d{2}", v):
        return None
    h, m = v.split(":")
    return int(h) * 60 + int(m)


def minutes_to_hhmm(total):
    total = int(total or 0)
    sign = "-" if total < 0 else ""
    total = abs(total)
    return f"{sign}{total // 60:02d}:{total % 60:02d}"


def normalize_shift(start_time, end_time):
    s = (start_time or "").strip()
    e = (end_time or "").strip()
    if re.fullmatch(r"\d{1,2}", s):
        s = f"{int(s):02d}:00"
    if re.fullmatch(r"\d{1,2}", e):
        e = f"{int(e):02d}:00"
    if not re.fullmatch(r"\d{1,2}:\d{2}", s) or not re.fullmatch(r"\d{1,2}:\d{2}", e):
        return "", ""
    s = f"{int(s.split(':')[0]):02d}:{s.split(':')[1]}"
    e = f"{int(e.split(':')[0]):02d}:{e.split(':')[1]}"
    return s, e


def summarize_day(entries):
    ranges = []
    for r in entries:
        st = time_to_minutes(r["start_time"])
        et = time_to_minutes(r["end_time"])
        if st is None or et is None:
            continue
        if et < st:
            et += 24 * 60
        ranges.append((st, et))
    if not ranges:
        return {"worked": 0, "break": 0}
    ranges.sort(key=lambda x: x[0])
    worked = sum(et - st for st, et in ranges)
    span = ranges[-1][1] - ranges[0][0]
    brk = max(0, span - worked)
    if len(ranges) == 1 and span >= 13 * 60 and brk == 0:
        brk = 60
        worked = max(0, worked - 60)
    return {"worked": worked, "break": brk}


def payroll_for_minutes(worked_minutes, rate):
    base_m = int(OVERTIME_CFG["base_hours"] * 60)
    t1_m = int(OVERTIME_CFG["tier1_hours"] * 60)
    t2_m = int(OVERTIME_CFG["tier2_hours"] * 60)
    base = min(worked_minutes, base_m)
    rem = max(0, worked_minutes - base_m)
    t1 = min(rem, t1_m)
    rem = max(0, rem - t1_m)
    t2 = min(rem, t2_m)
    rem = max(0, rem - t2_m)
    after = rem
    return (
        (base / 60.0) * rate * (OVERTIME_CFG["base_percent"] / 100.0)
        + (t1 / 60.0) * rate * (OVERTIME_CFG["tier1_percent"] / 100.0)
        + (t2 / 60.0) * rate * (OVERTIME_CFG["tier2_percent"] / 100.0)
        + (after / 60.0) * rate * (OVERTIME_CFG["after_percent"] / 100.0)
    )


def split_band_minutes(worked_minutes):
    base_m = int(OVERTIME_CFG["base_hours"] * 60)
    t1_m = int(OVERTIME_CFG["tier1_hours"] * 60)
    t2_m = int(OVERTIME_CFG["tier2_hours"] * 60)
    base = min(worked_minutes, base_m)
    rem = max(0, worked_minutes - base_m)
    t1 = min(rem, t1_m)
    rem = max(0, rem - t1_m)
    t2 = min(rem, t2_m)
    rem = max(0, rem - t2_m)
    after = rem
    return base, t1, t2, after


def festival_overlap_minutes(entry):
    if not int(entry["festival_enabled"] or 0):
        return 0
    fst, fet = normalize_shift(entry["festival_start_time"] or "", entry["festival_end_time"] or "")
    if not fst or not fet:
        return 0
    st = time_to_minutes(entry["start_time"])
    et = time_to_minutes(entry["end_time"])
    fs = time_to_minutes(fst)
    fe = time_to_minutes(fet)
    if None in (st, et, fs, fe):
        return 0
    if et < st:
        et += 24 * 60
    if fe < fs:
        fe += 24 * 60
    return max(0, min(et, fe) - max(st, fs))


def monthly_payroll(rows, rate):
    by_date = {}
    for r in rows:
        by_date.setdefault(r["work_date"], []).append(r)
    worked = 0
    brk = 0
    gross = 0.0
    festival_premium = 0.0
    band_base = 0
    band_125 = 0
    band_150 = 0
    festival_minutes_total = 0
    for entries in by_date.values():
        s = summarize_day(entries)
        worked += s["worked"]
        brk += s["break"]
        gross += payroll_for_minutes(s["worked"], rate)
        b0, b1, b2, b3 = split_band_minutes(s["worked"])
        band_base += b0
        band_125 += b1
        band_150 += (b2 + b3)
        for e in entries:
            fmin = festival_overlap_minutes(e)
            festival_minutes_total += fmin
            fpercent = float(e["festival_percent"] or 150.0)
            festival_premium += (fmin / 60.0) * rate * max(0.0, (fpercent - 100.0) / 100.0)
    gross += festival_premium
    tax = gross * INCOME_TAX_RATE
    accommodation = ACCOMMODATION_DEDUCTION_ILS
    total_deductions = tax + accommodation
    transport = TRANSPORT_ALLOWANCE_ILS
    net_before_transport = gross - total_deductions
    net = net_before_transport + transport
    return {
        "worked": minutes_to_hhmm(worked),
        "break": minutes_to_hhmm(brk),
        "h125": minutes_to_hhmm(band_125),
        "h150": minutes_to_hhmm(band_150),
        "festival_hours": minutes_to_hhmm(festival_minutes_total),
        "festival_premium": round(festival_premium, 2),
        "gross": round(gross, 2),
        "transport": round(transport, 2),
        "net_before_transport": round(net_before_transport, 2),
        "tax": round(tax, 2),
        "accommodation": round(accommodation, 2),
        "total_deductions": round(total_deductions, 2),
        "net": round(net, 2),
    }


def generate_otp():
    return f"{secrets.randbelow(1_000_000):06d}"


def send_reset_otp_email(to_email, otp_code):
    if not (SMTP_HOST and SMTP_USER and SMTP_PASS):
        return False, "Email server is not configured yet."
    msg = EmailMessage()
    msg["Subject"] = "Your Password Reset OTP"
    msg["From"] = SMTP_FROM
    msg["To"] = to_email
    msg.set_content(f"Your OTP for password reset is: {otp_code}\n\nThis OTP expires in 10 minutes.")
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
        return True, ""
    except Exception:
        return False, "Unable to send OTP email. Check SMTP settings."

def tr(lang, key):
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, TRANSLATIONS["en"].get(key, key))


def render_shell(title, content, user=None, lang="en"):
    nav = f'<a href="/?lang={lang}">{tr(lang,"home")}</a><a href="/dashboard?lang={lang}">{tr(lang,"dashboard")}</a>'
    nav += f'<a href="/logout?lang={lang}">{tr(lang,"logout")}</a>' if user else f'<a href="/login?lang={lang}">{tr(lang,"login")}</a><a href="/register?lang={lang}">{tr(lang,"register")}</a>'
    return f"""<!doctype html><html lang="en"><head>
    <meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{html.escape(title)}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&display=swap" rel="stylesheet" />
    <link rel="stylesheet" href="/static/style.css" />
</head><body>
    <header class="topbar"><div class="brand"><img src="/static/namaste.jpeg" alt="Namaste logo" class="brand-logo" />Salary Calendar</div><nav>{nav}</nav></header>
    <main class="container">{content}</main><footer class="site-footer">Created with &hearts; santosh</footer>
    <script>
    (function() {{
      function toggleFestivalFields(checkEl) {{
        var container = checkEl.closest("td, form, div");
        if (!container) return;
        var fields = container.querySelector(".festival-fields");
        if (!fields) return;
        fields.classList.toggle("hidden", !checkEl.checked);
      }}
      function wire() {{
        document.querySelectorAll('input[name="festival_enabled"]').forEach(function(chk) {{
          chk.addEventListener("change", function() {{ toggleFestivalFields(chk); }});
          toggleFestivalFields(chk);
        }});
        var nf = document.getElementById("new-festival-check");
        var nff = document.getElementById("new-festival-fields");
        if (nf && nff) {{
          var fn = function() {{ nff.classList.toggle("hidden", !nf.checked); }};
          nf.addEventListener("change", fn);
          fn();
        }}
      }}
      if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", wire);
      else wire();
    }})();
    </script>
</body></html>"""


def card(title, body):
    return f'<section class="card"><h2>{html.escape(title)}</h2>{body}</section>'


class AppHandler(BaseHTTPRequestHandler):
    def get_lang(self, user=None):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        q_lang = (q.get("lang", [""])[0] or "").strip().lower()
        valid = {code for code, _ in LANGUAGE_OPTIONS}
        if q_lang in valid:
            if user:
                conn = db_conn()
                conn.execute("UPDATE users SET language = ? WHERE id = ?", (q_lang, user["id"]))
                conn.commit()
                conn.close()
            return q_lang
        if user and "language" in user.keys() and user["language"] in valid:
            return user["language"]
        return "en"

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path.startswith("/static/"):
            return self.serve_static(path)
        if path == "/":
            return self.handle_home()
        if path == "/register":
            return self.handle_register_form()
        if path == "/login":
            return self.handle_login_form()
        if path == "/forgot-password":
            return self.handle_forgot_password_form()
        if path == "/verify-otp":
            return self.handle_verify_otp_form()
        if path == "/reset-password":
            return self.handle_reset_password_form()
        if path == "/logout":
            return self.handle_logout()
        if path == "/dashboard":
            return self.handle_dashboard()
        if path == "/health":
            return self.respond(200, "ok", content_type="text/plain")
        self.respond(404, render_shell("Not Found", card("404", "<p>Page not found.</p>")))

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/register":
            return self.handle_register_submit()
        if path == "/login":
            return self.handle_login_submit()
        if path == "/forgot-password":
            return self.handle_forgot_password_submit()
        if path == "/verify-otp":
            return self.handle_verify_otp_submit()
        if path == "/reset-password":
            return self.handle_reset_password_submit()
        if path == "/entry-add":
            return self.handle_entry_add()
        if path == "/entry-update":
            return self.handle_entry_update()
        if path == "/entry-delete":
            return self.handle_entry_delete()
        if path == "/settings-rate":
            return self.handle_settings_rate()
        if path == "/settings-language":
            return self.handle_settings_language()
        self.respond(404, render_shell("Not Found", card("404", "<p>Page not found.</p>")))

    def handle_home(self):
        user = self.current_user()
        lang = self.get_lang(user)
        self.respond(200, render_shell("Salary Calendar", f"""
        <section class="hero"><h1>{html.escape(tr(lang, "manual_salary_calendar"))}</h1>
        <p>{html.escape(tr(lang, "calendar_desc"))}</p>
        <div class="hero-actions"><a class="btn" href="/dashboard?lang={lang}">{html.escape(tr(lang, "open_calendar"))}</a></div></section>
        """, user=user, lang=lang))

    def handle_register_form(self, error=""):
        lang = self.get_lang(None)
        b = f"""<form method="POST" class="form">
        <input type="hidden" name="lang" value="{lang}" />
        <label>{html.escape(tr(lang, "full_name"))} <input name="full_name" required /></label>
        <label>{html.escape(tr(lang, "email"))} <input type="email" name="email" required /></label>
        <label>{html.escape(tr(lang, "password"))} <input type="password" name="password" minlength="6" required /></label>
        <button class="btn" type="submit">{html.escape(tr(lang, "register"))}</button><p class="error">{html.escape(error)}</p></form>"""
        self.respond(200, render_shell("Register", card(tr(lang, "create_account"), b), lang=lang))

    def handle_register_submit(self):
        f = self.read_urlencoded()
        lang = (f.get("lang") or "en").strip().lower()
        if lang not in {c for c, _ in LANGUAGE_OPTIONS}:
            lang = "en"
        name = (f.get("full_name") or "").strip()
        email = (f.get("email") or "").strip().lower()
        password = f.get("password") or ""
        if not name or not email or len(password) < 6:
            return self.handle_register_form("Please fill all fields (password min 6 chars).")
        conn = db_conn()
        try:
            conn.execute("INSERT INTO users(full_name, email, password_hash, hourly_rate, language, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                         (name, email, hash_password(password), 45.0, lang, datetime.utcnow().isoformat()))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return self.handle_register_form("Email already exists.")
        conn.close()
        self.redirect(f"/login?lang={lang}")

    def handle_login_form(self, error=""):
        lang = self.get_lang(None)
        b = f"""<form method="POST" class="form">
        <input type="hidden" name="lang" value="{lang}" />
        <label>{html.escape(tr(lang, "email"))} <input type="email" name="email" required /></label>
        <label>{html.escape(tr(lang, "password"))} <input type="password" name="password" required /></label>
        <button class="btn" type="submit">{html.escape(tr(lang, "login"))}</button>
        <a class="btn secondary tiny" href="/forgot-password?lang={lang}">{html.escape(tr(lang, "forgot_password"))}</a>
        <p class="error">{html.escape(error)}</p></form>"""
        self.respond(200, render_shell("Login", card(tr(lang, "welcome_back"), b), lang=lang))

    def handle_login_submit(self):
        f = self.read_urlencoded()
        lang = (f.get("lang") or "en").strip().lower()
        if lang not in {c for c, _ in LANGUAGE_OPTIONS}:
            lang = "en"
        email = (f.get("email") or "").strip().lower()
        password = f.get("password") or ""
        conn = db_conn()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        if not user or not verify_password(password, user["password_hash"]):
            return self.handle_login_form("Invalid credentials.")
        conn = db_conn()
        conn.execute("UPDATE users SET language = ? WHERE id = ?", (lang, user["id"]))
        conn.commit()
        conn.close()
        self.start_session(user["id"])

    def handle_forgot_password_form(self, error="", success=""):
        lang = self.get_lang(None)
        b = f"""<form method="POST" class="form">
        <input type="hidden" name="lang" value="{lang}" />
        <label>{html.escape(tr(lang, "email"))} <input type="email" name="email" required /></label>
        <button class="btn" type="submit">{html.escape(tr(lang, "send_otp"))}</button>
        <p class="error">{html.escape(error)}</p><p class="muted">{html.escape(success)}</p></form>"""
        self.respond(200, render_shell("Forgot Password", card(tr(lang, "forgot_password"), b), lang=lang))

    def handle_forgot_password_submit(self):
        f = self.read_urlencoded()
        lang = (f.get("lang") or "en").strip().lower()
        email = (f.get("email") or "").strip().lower()
        conn = db_conn()
        user = conn.execute("SELECT id, email FROM users WHERE email = ?", (email,)).fetchone()
        if not user:
            conn.close()
            return self.handle_forgot_password_form("No account found for this email.")
        otp = generate_otp()
        exp = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
        conn.execute("INSERT INTO password_resets(user_id, otp_code, expires_at, used, created_at) VALUES (?, ?, ?, 0, ?)",
                     (user["id"], otp, exp, datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()
        ok, msg = send_reset_otp_email(user["email"], otp)
        if not ok:
            return self.handle_forgot_password_form(msg)
        self.redirect(f"/verify-otp?email={urllib.parse.quote(user['email'])}&lang={lang}")

    def handle_verify_otp_form(self, error="", email=""):
        if not email:
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            email = (q.get("email", [""])[0] or "").strip().lower()
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        lang = (q.get("lang", ["en"])[0] or "en").strip().lower()
        b = f"""<form method="POST" class="form">
        <input type="hidden" name="email" value="{html.escape(email)}" />
        <input type="hidden" name="lang" value="{lang}" />
        <label>{html.escape(tr(lang, "email"))} <input type="email" value="{html.escape(email)}" disabled /></label>
        <label>OTP <input name="otp_code" pattern="\\d{{6}}" minlength="6" maxlength="6" required /></label>
        <button class="btn" type="submit">{html.escape(tr(lang, "verify_otp"))}</button><p class="error">{html.escape(error)}</p></form>"""
        self.respond(200, render_shell("Verify OTP", card(tr(lang, "verify_otp"), b), lang=lang))

    def handle_verify_otp_submit(self):
        f = self.read_urlencoded()
        lang = (f.get("lang") or "en").strip().lower()
        email = (f.get("email") or "").strip().lower()
        otp = (f.get("otp_code") or "").strip()
        conn = db_conn()
        user = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if not user:
            conn.close()
            return self.handle_verify_otp_form("Invalid email.", email=email)
        reset = conn.execute("SELECT * FROM password_resets WHERE user_id = ? AND otp_code = ? AND used = 0 ORDER BY id DESC LIMIT 1",
                             (user["id"], otp)).fetchone()
        conn.close()
        if not reset:
            return self.handle_verify_otp_form("Invalid OTP.", email=email)
        if datetime.utcnow() > datetime.fromisoformat(reset["expires_at"]):
            return self.handle_verify_otp_form("OTP expired. Please request a new one.", email=email)
        self.redirect(f"/reset-password?email={urllib.parse.quote(email)}&otp={urllib.parse.quote(otp)}&lang={lang}")

    def handle_reset_password_form(self, error="", email="", otp=""):
        if not email or not otp:
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            email = email or (q.get("email", [""])[0] or "").strip().lower()
            otp = otp or (q.get("otp", [""])[0] or "").strip()
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        lang = (q.get("lang", ["en"])[0] or "en").strip().lower()
        b = f"""<form method="POST" class="form">
        <input type="hidden" name="email" value="{html.escape(email)}" />
        <input type="hidden" name="otp" value="{html.escape(otp)}" />
        <input type="hidden" name="lang" value="{lang}" />
        <label>{html.escape(tr(lang, "new_password"))} <input type="password" name="password" minlength="6" required /></label>
        <label>{html.escape(tr(lang, "confirm_password"))} <input type="password" name="confirm_password" minlength="6" required /></label>
        <button class="btn" type="submit">{html.escape(tr(lang, "reset_password"))}</button><p class="error">{html.escape(error)}</p></form>"""
        self.respond(200, render_shell("Reset Password", card(tr(lang, "reset_password"), b), lang=lang))

    def handle_reset_password_submit(self):
        f = self.read_urlencoded()
        email = (f.get("email") or "").strip().lower()
        otp = (f.get("otp") or "").strip()
        p = f.get("password") or ""
        cp = f.get("confirm_password") or ""
        if len(p) < 6:
            return self.handle_reset_password_form("Password must be at least 6 characters.", email=email, otp=otp)
        if p != cp:
            return self.handle_reset_password_form("Passwords do not match.", email=email, otp=otp)
        conn = db_conn()
        user = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if not user:
            conn.close()
            return self.handle_reset_password_form("Invalid account.", email=email, otp=otp)
        reset = conn.execute("SELECT * FROM password_resets WHERE user_id = ? AND otp_code = ? AND used = 0 ORDER BY id DESC LIMIT 1",
                             (user["id"], otp)).fetchone()
        if not reset:
            conn.close()
            return self.handle_reset_password_form("Invalid OTP.", email=email, otp=otp)
        if datetime.utcnow() > datetime.fromisoformat(reset["expires_at"]):
            conn.close()
            return self.handle_reset_password_form("OTP expired. Please request a new one.", email=email, otp=otp)
        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(p), user["id"]))
        conn.execute("UPDATE password_resets SET used = 1 WHERE id = ?", (reset["id"],))
        conn.commit()
        conn.close()
        self.redirect("/login")

    def handle_logout(self):
        jar = cookies.SimpleCookie(self.headers.get("Cookie"))
        sid = jar.get("sid")
        if sid and sid.value in SESSIONS:
            del SESSIONS[sid.value]
        self.send_response(302)
        self.send_header("Location", "/")
        self.send_header("Set-Cookie", "sid=; HttpOnly; Path=/; Max-Age=0")
        self.end_headers()

    def handle_dashboard(self):
        user = self.current_user()
        if not user:
            return self.redirect("/login")
        lang = self.get_lang(user)
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        month_q = (q.get("month", [""])[0] or "").strip()
        selected_date = (q.get("date", [""])[0] or "").strip()
        first, last = month_bounds(month_q)
        month_token = first.strftime("%Y-%m")
        prev_month, next_month = prev_next_month(month_token)
        if not selected_date:
            selected_date = first.isoformat()
        conn = db_conn()
        rows = conn.execute("SELECT * FROM work_entries WHERE user_id = ? AND work_date >= ? AND work_date <= ? ORDER BY work_date ASC, start_time ASC",
                            (user["id"], first.isoformat(), last.isoformat())).fetchall()
        conn.close()
        by_date = {}
        for r in rows:
            by_date.setdefault(r["work_date"], []).append(r)
        rate = float(user["hourly_rate"] or 45.0)
        month_pay = monthly_payroll(rows, rate)

        weeks = calendar.Calendar(firstweekday=6).monthdatescalendar(first.year, first.month)
        tiles = ""
        for week in weeks:
            for d in week:
                d_iso = d.isoformat()
                entries = by_date.get(d_iso, [])
                s = summarize_day(entries)
                worked_txt = minutes_to_hhmm(s["worked"]) if entries else "-"
                hover = f"Worked {worked_txt}, Break {minutes_to_hhmm(s['break'])}, Entries {len(entries)}"
                cls = "cal-day"
                if d.month != first.month:
                    cls += " muted-day"
                if d_iso == selected_date:
                    cls += " active-day"
                tiles += f'<a class="{cls}" href="/dashboard?month={month_token}&date={d_iso}&lang={lang}" title="{html.escape(hover)}"><span class="day-num">{d.day}</span><span class="day-hours">{worked_txt}</span></a>'

        selected_rows = by_date.get(selected_date, [])
        entry_rows = ""
        for r in selected_rows:
            fest_checked = "checked" if int(r["festival_enabled"] or 0) else ""
            fest_start = html.escape(r["festival_start_time"] or "")
            fest_end = html.escape(r["festival_end_time"] or "")
            fest_percent = html.escape(str(r["festival_percent"] or 150))
            entry_rows += f"""
            <tr><td>{html.escape(r["start_time"])}</td><td>{html.escape(r["end_time"])}</td><td>{html.escape(r["notes"] or "-")}</td>
            <td>
                <label class="fest-check"><input type="checkbox" form="upd-{r["id"]}" name="festival_enabled" {fest_checked} /> {html.escape(tr(lang, "festival"))}</label>
                <div class="festival-fields {'' if int(r['festival_enabled'] or 0) else 'hidden'}" data-target="upd-{r["id"]}">
                    <label>{html.escape(tr(lang, "from"))}
                        <input form="upd-{r["id"]}" name="festival_start_time" value="{fest_start}" placeholder="00:00" />
                    </label>
                    <label>{html.escape(tr(lang, "to"))}
                        <input form="upd-{r["id"]}" name="festival_end_time" value="{fest_end}" placeholder="00:00" />
                    </label>
                    <label>{html.escape(tr(lang, "rate_percent"))}
                        <input form="upd-{r["id"]}" name="festival_percent" value="{fest_percent}" placeholder="150" />
                    </label>
                </div>
            </td><td>
            <form id="upd-{r["id"]}" method="POST" action="/entry-update" class="inline-editor">
                <input type="hidden" name="entry_id" value="{r["id"]}" />
                <input type="hidden" name="month" value="{month_token}" />
                <input type="hidden" name="date" value="{selected_date}" />
                <input type="hidden" name="lang" value="{lang}" />
                <input name="start_time" value="{html.escape(r["start_time"])}" placeholder="00:00" required />
                <input name="end_time" value="{html.escape(r["end_time"])}" placeholder="00:00" required />
                <input name="notes" value="{html.escape(r["notes"] or "")}" placeholder="Notes" />
                <button class="btn tiny" type="submit">{html.escape(tr(lang, "save"))}</button>
            </form>
            <form method="POST" action="/entry-delete" class="inline-editor">
                <input type="hidden" name="entry_id" value="{r["id"]}" />
                <input type="hidden" name="month" value="{month_token}" />
                <input type="hidden" name="date" value="{selected_date}" />
                <input type="hidden" name="lang" value="{lang}" />
                <button class="btn danger tiny" type="submit">{html.escape(tr(lang, "delete"))}</button>
            </form></td></tr>"""
        if not entry_rows:
            entry_rows = "<tr><td colspan='5'>No entries for this day. Add below.</td></tr>"

        language_select = "".join(
            f'<option value="{code}" {"selected" if code == lang else ""}>{label}</option>' for code, label in LANGUAGE_OPTIONS
        )

        cal_html = f"""<div class="calendar-head"><a class="btn secondary tiny" href="/dashboard?month={prev_month}&date={selected_date}&lang={lang}">{html.escape(tr(lang, "previous"))}</a><h3>{html.escape(first.strftime("%B %Y"))}</h3><a class="btn secondary tiny" href="/dashboard?month={next_month}&date={selected_date}&lang={lang}">{html.escape(tr(lang, "next"))}</a></div>
        <div class="weekday-row"><span>Sun</span><span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span></div><div class="calendar-grid">{tiles}</div>"""
        pay_html = f"""<form method="POST" action="/settings-rate" class="manual-add">
            <input type="hidden" name="month" value="{month_token}" /><input type="hidden" name="date" value="{selected_date}" /><input type="hidden" name="lang" value="{lang}" />
            <label>{html.escape(tr(lang, "base_rate"))} <input type="number" name="hourly_rate" step="0.01" min="0" value="{rate}" required /></label>
            <button class="btn tiny" type="submit">{html.escape(tr(lang, "save_rate"))}</button></form>
            <form method="POST" action="/settings-language" class="manual-add"><input type="hidden" name="month" value="{month_token}" /><input type="hidden" name="date" value="{selected_date}" />
            <label>{html.escape(tr(lang, "lang"))}<select name="language">{language_select}</select></label><button class="btn tiny" type="submit">{html.escape(tr(lang, "save"))}</button></form>
            <div class="kpis"><div class="kpi"><strong>{month_pay["worked"]}</strong><span>{html.escape(tr(lang, "total_worked"))}</span></div><div class="kpi"><strong>{month_pay["break"]}</strong><span>{html.escape(tr(lang, "total_break"))}</span></div><div class="kpi"><strong>{month_pay["h125"]}</strong><span>{html.escape(tr(lang, "h125"))}</span></div><div class="kpi"><strong>{month_pay["h150"]}</strong><span>{html.escape(tr(lang, "h150"))}</span></div><div class="kpi"><strong>{month_pay["festival_hours"]}</strong><span>{html.escape(tr(lang, "festival_hours"))}</span></div><div class="kpi"><strong>{month_pay["festival_premium"]}</strong><span>{html.escape(tr(lang, "festival_premium"))}</span></div><div class="kpi"><strong>{month_pay["gross"]}</strong><span>{html.escape(tr(lang, "gross_salary"))}</span></div><div class="kpi"><strong>{month_pay["tax"]}</strong><span>{html.escape(tr(lang, "income_tax"))}</span></div><div class="kpi"><strong>{month_pay["accommodation"]}</strong><span>{html.escape(tr(lang, "accommodation"))}</span></div><div class="kpi"><strong>{month_pay["total_deductions"]}</strong><span>{html.escape(tr(lang, "total_deductions"))}</span></div><div class="kpi"><strong>{month_pay["net_before_transport"]}</strong><span>{html.escape(tr(lang, "after_deductions"))}</span></div><div class="kpi"><strong>{month_pay["transport"]}</strong><span>{html.escape(tr(lang, "transport"))}</span></div><div class="kpi"><strong>{month_pay["net"]}</strong><span>{html.escape(tr(lang, "final_net"))}</span></div></div>"""
        day_html = f"""<h4>{html.escape(tr(lang, "entries_for"))} {html.escape(selected_date)}</h4><table><thead><tr><th>{html.escape(tr(lang, "start"))}</th><th>{html.escape(tr(lang, "end"))}</th><th>{html.escape(tr(lang, "notes"))}</th><th>{html.escape(tr(lang, "festival"))}</th><th>{html.escape(tr(lang, "actions"))}</th></tr></thead><tbody>{entry_rows}</tbody></table>
            <form method="POST" action="/entry-add" class="manual-add">
                <input type="hidden" name="month" value="{month_token}" /><input type="hidden" name="lang" value="{lang}" /><input type="date" name="work_date" value="{selected_date}" required />
                <input name="start_time" placeholder="00:00" required /><input name="end_time" placeholder="00:00" required />
                <input name="notes" placeholder="{html.escape(tr(lang, "notes"))}" />
                <label class="fest-check"><input type="checkbox" name="festival_enabled" id="new-festival-check" /> {html.escape(tr(lang, "festival"))}</label>
                <div class="festival-fields hidden" id="new-festival-fields">
                    <label>{html.escape(tr(lang, "from"))}
                        <input name="festival_start_time" placeholder="00:00" />
                    </label>
                    <label>{html.escape(tr(lang, "to"))}
                        <input name="festival_end_time" placeholder="00:00" />
                    </label>
                    <label>{html.escape(tr(lang, "rate_percent"))}
                        <input name="festival_percent" value="150" placeholder="150" />
                    </label>
                </div>
                <button class="btn tiny" type="submit">{html.escape(tr(lang, "add_entry"))}</button></form>"""
        body = card(f"{html.escape(tr(lang, 'hello'))}, {user['full_name']}", "<p>Calendar-first duty tracking with monthly salary calculation.</p>") + card(tr(lang, "work_calendar"), cal_html) + card(tr(lang, "monthly_payroll"), pay_html) + card(tr(lang, "day_editor"), day_html)
        self.respond(200, render_shell("Dashboard", body, user=user, lang=lang))

    def handle_entry_add(self):
        user = self.current_user()
        if not user:
            return self.redirect("/login")
        f = self.read_urlencoded()
        lang = (f.get("lang") or "en").strip().lower()
        month = (f.get("month") or "").strip()
        work_date = (f.get("work_date") or "").strip()
        st, et = normalize_shift(f.get("start_time"), f.get("end_time"))
        notes = (f.get("notes") or "").strip()
        festival_enabled = 1 if f.get("festival_enabled") == "on" else 0
        fst, fet = normalize_shift(f.get("festival_start_time"), f.get("festival_end_time"))
        try:
            festival_percent = float(f.get("festival_percent") or "150")
            if festival_percent < 0:
                raise ValueError
        except ValueError:
            festival_percent = 150.0
        rate = float(user["hourly_rate"] or 45.0)
        try:
            datetime.strptime(work_date, "%Y-%m-%d")
            if not st or not et:
                raise ValueError
        except ValueError:
            return self.redirect(f"/dashboard?month={urllib.parse.quote(month)}&date={urllib.parse.quote(work_date)}&lang={urllib.parse.quote(lang)}")
        now = datetime.utcnow().isoformat()
        conn = db_conn()
        conn.execute(
            """
            INSERT INTO work_entries(user_id, work_date, start_time, end_time, notes, hourly_rate, festival_enabled, festival_start_time, festival_end_time, festival_percent, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user["id"], work_date, st, et, notes, rate, festival_enabled, fst if festival_enabled else "", fet if festival_enabled else "", festival_percent, now, now),
        )
        conn.commit()
        conn.close()
        self.redirect(f"/dashboard?month={urllib.parse.quote(month)}&date={urllib.parse.quote(work_date)}&lang={urllib.parse.quote(lang)}")

    def handle_entry_update(self):
        user = self.current_user()
        if not user:
            return self.redirect("/login")
        f = self.read_urlencoded()
        lang = (f.get("lang") or "en").strip().lower()
        month = (f.get("month") or "").strip()
        selected_date = (f.get("date") or "").strip()
        try:
            entry_id = int(f.get("entry_id") or "0")
        except ValueError:
            return self.redirect(f"/dashboard?lang={urllib.parse.quote(lang)}")
        st, et = normalize_shift(f.get("start_time"), f.get("end_time"))
        if not st or not et:
            return self.redirect(f"/dashboard?month={urllib.parse.quote(month)}&date={urllib.parse.quote(selected_date)}&lang={urllib.parse.quote(lang)}")
        notes = (f.get("notes") or "").strip()
        festival_enabled = 1 if f.get("festival_enabled") == "on" else 0
        fst, fet = normalize_shift(f.get("festival_start_time"), f.get("festival_end_time"))
        try:
            festival_percent = float(f.get("festival_percent") or "150")
            if festival_percent < 0:
                raise ValueError
        except ValueError:
            festival_percent = 150.0
        conn = db_conn()
        conn.execute(
            """
            UPDATE work_entries
            SET start_time = ?, end_time = ?, notes = ?, festival_enabled = ?, festival_start_time = ?, festival_end_time = ?, festival_percent = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (st, et, notes, festival_enabled, fst if festival_enabled else "", fet if festival_enabled else "", festival_percent, datetime.utcnow().isoformat(), entry_id, user["id"]),
        )
        conn.commit()
        conn.close()
        self.redirect(f"/dashboard?month={urllib.parse.quote(month)}&date={urllib.parse.quote(selected_date)}&lang={urllib.parse.quote(lang)}")

    def handle_entry_delete(self):
        user = self.current_user()
        if not user:
            return self.redirect("/login")
        f = self.read_urlencoded()
        lang = (f.get("lang") or "en").strip().lower()
        month = (f.get("month") or "").strip()
        selected_date = (f.get("date") or "").strip()
        try:
            entry_id = int(f.get("entry_id") or "0")
        except ValueError:
            return self.redirect(f"/dashboard?lang={urllib.parse.quote(lang)}")
        conn = db_conn()
        conn.execute("DELETE FROM work_entries WHERE id = ? AND user_id = ?", (entry_id, user["id"]))
        conn.commit()
        conn.close()
        self.redirect(f"/dashboard?month={urllib.parse.quote(month)}&date={urllib.parse.quote(selected_date)}&lang={urllib.parse.quote(lang)}")

    def handle_settings_rate(self):
        user = self.current_user()
        if not user:
            return self.redirect("/login")
        f = self.read_urlencoded()
        lang = (f.get("lang") or "en").strip().lower()
        month = (f.get("month") or "").strip()
        selected_date = (f.get("date") or "").strip()
        try:
            rate = float(f.get("hourly_rate") or "45")
            if rate < 0:
                raise ValueError
        except ValueError:
            rate = float(user["hourly_rate"] or 45.0)
        conn = db_conn()
        conn.execute("UPDATE users SET hourly_rate = ? WHERE id = ?", (rate, user["id"]))
        conn.commit()
        conn.close()
        self.redirect(f"/dashboard?month={urllib.parse.quote(month)}&date={urllib.parse.quote(selected_date)}&lang={urllib.parse.quote(lang)}")

    def handle_settings_language(self):
        user = self.current_user()
        if not user:
            return self.redirect("/login")
        f = self.read_urlencoded()
        month = (f.get("month") or "").strip()
        selected_date = (f.get("date") or "").strip()
        lang = (f.get("language") or "en").strip().lower()
        if lang not in {c for c, _ in LANGUAGE_OPTIONS}:
            lang = "en"
        conn = db_conn()
        conn.execute("UPDATE users SET language = ? WHERE id = ?", (lang, user["id"]))
        conn.commit()
        conn.close()
        self.redirect(f"/dashboard?month={urllib.parse.quote(month)}&date={urllib.parse.quote(selected_date)}&lang={urllib.parse.quote(lang)}")

    def current_user(self):
        jar = cookies.SimpleCookie(self.headers.get("Cookie"))
        sid = jar.get("sid")
        if not sid or sid.value not in SESSIONS:
            return None
        user_id = SESSIONS[sid.value]
        conn = db_conn()
        user = conn.execute("SELECT id, full_name, email, hourly_rate, language FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        return user

    def start_session(self, user_id):
        sid = secrets.token_urlsafe(24)
        SESSIONS[sid] = user_id
        self.send_response(302)
        self.send_header("Location", "/dashboard")
        self.send_header("Set-Cookie", f"sid={sid}; HttpOnly; Path=/")
        self.end_headers()

    def read_urlencoded(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        parsed = urllib.parse.parse_qs(body)
        return {k: v[0] for k, v in parsed.items()}

    def serve_static(self, path):
        file_path = os.path.join(BASE_DIR, path.lstrip("/"))
        if not os.path.isfile(file_path):
            return self.respond(404, "Not found", content_type="text/plain")
        if file_path.endswith(".css"):
            ctype = "text/css"
        elif file_path.endswith(".jpeg") or file_path.endswith(".jpg"):
            ctype = "image/jpeg"
        elif file_path.endswith(".png"):
            ctype = "image/png"
        else:
            ctype = "application/octet-stream"
        with open(file_path, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, location):
        self.send_response(302)
        self.send_header("Location", location)
        self.end_headers()

    def respond(self, status, body, content_type="text/html; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.wfile.write(body)


if __name__ == "__main__":
    os.makedirs(STATIC_DIR, exist_ok=True)
    init_db()
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", str(PORT)))
    print(f"Server running on http://{host}:{port}")
    HTTPServer((host, port), AppHandler).serve_forever()
