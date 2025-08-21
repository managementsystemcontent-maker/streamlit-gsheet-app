import os
from datetime import date, datetime, timedelta
import pandas as pd
from dotenv import load_dotenv

from sheets_utils import read_plan
from email_utils import send_email
from calendar_utils import make_ics_event

load_dotenv()

TZ = os.getenv("TIMEZONE", "Asia/Jakarta")

df = read_plan()
if df.empty:
    print("[INFO] Plan empty. Exiting.")
    raise SystemExit(0)

# Normalize date/time
df["Tanggal Post"] = pd.to_datetime(df["Tanggal Post"], errors="coerce").dt.date
# keep jam as string "HH:MM"
def to_dt(d, jam):
    try:
        hh, mm = str(jam or "09:00").split(":")
        return datetime(d.year, d.month, d.day, int(hh), int(mm))
    except Exception:
        return datetime(d.year, d.month, d.day, 9, 0)

today = date.today()
tomorrow = today + timedelta(days=1)

today_df = df[df["Tanggal Post"] == today]
tomorrow_df = df[df["Tanggal Post"] == tomorrow]

if today_df.empty and tomorrow_df.empty and os.getenv("SEND_EMPTY","false").lower()!="true":
    print("[INFO] No items today/tomorrow. Email not sent.")
    raise SystemExit(0)

def rows_to_html(subset: pd.DataFrame) -> str:
    if subset.empty:
        return "<p><em>Tidak ada.</em></p>"
    rows = []
    for _, r in subset.iterrows():
        title = r.get("Judul Konten","(tanpa judul)")
        desc = r.get("Description","")
        plat = r.get("Platform","-")
        tgl = r.get("Tanggal Post","")
        jam = r.get("Jam Post","")
        status = r.get("Status","-")
        notes = r.get("Notes","")
        link = (r.get("Link Asset","") or "").strip()
        judul_cell = f"<a href='{link}'>{title}</a>" if link else title
        rows.append(f"<tr><td>{judul_cell}</td><td>{desc}</td><td>{plat}</td><td>{tgl}</td><td>{jam}</td><td>{status}</td><td>{notes}</td></tr>")
    return "<table border='1' cellpadding='6' cellspacing='0'><tr><th>Judul</th><th>Description</th><th>Platform</th><th>Tanggal</th><th>Jam</th><th>Status</th><th>Notes</th></tr>" + "".join(rows) + "</table>"

html = f"""
<html><body>
<p>Hai Fitria 👋, ini reminder konten untuk <b>{today.strftime('%A, %d %B %Y')}</b> dan <b>{tomorrow.strftime('%A, %d %B %Y')}</b>.</p>
<h3>Hari ini</h3>
{rows_to_html(today_df)}
<h3>Besok</h3>
{rows_to_html(tomorrow_df)}
<p>Semangat! 💪</p>
</body></html>
"""

# Build ICS attachments per row (today + tomorrow)
atts = []
for subset in (today_df, tomorrow_df):
    for _, r in subset.iterrows():
        title = r.get("Judul Konten","(tanpa judul)")
        desc = r.get("Description","")
        d = r.get("Tanggal Post")
        jam = r.get("Jam Post","09:00")
        try:
            hh, mm = str(jam).split(":")
            start_dt = to_dt(d, jam)
        except Exception:
            start_dt = to_dt(d, "09:00")
        ics_bytes = make_ics_event(title, desc, start_dt, tz=TZ)
        fname = f"{d}-{title.replace(' ','_')}.ics"
        atts.append((fname, "text/calendar", ics_bytes))

to = os.getenv("EMAIL_TO")
subject = f"Reminder Konten — {today.isoformat()}"
send_email(subject, html, to, atts)
print("[OK] Email sent with ICS attachments.")

GSHEET_ID = "1IVzpOG7R7YD4F3geE06rbb8ouLwkeC53RUQPhUlbR-4"
GOOGLE_SERVICE_ACCOUNT_JSON = "content-management-fitria-37938e9747f9.json"