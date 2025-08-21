import streamlit as st
import gspread
import pandas as pd
from datetime import datetime
from ics import Calendar, Event

# =====================================================
# 🔑 SETUP GOOGLE SHEETS
# =====================================================
try:
    # Menggunakan st.secrets untuk kredensial yang lebih aman di Streamlit Cloud
    creds = st.secrets["gcp_service_account"]

    # Lingkup akses yang diperlukan
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    # Otorisasi gspread client
    client = gspread.service_account_from_dict(creds, scopes=scope)

except Exception as e:
    st.error(f"❌ Gagal memuat kredensial dari st.secrets: {e}")
    st.info("Pastikan Anda sudah menambahkan kredensial di Streamlit Secrets.")
    st.stop()

# Buka Google Sheet (ganti URL/ID sesuai kebutuhan)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1IVzpOG7R7YD4F3geE06rbb8ouLwkeC53RUQPhUlbR-4/edit"

try:
    sheet = client.open_by_url(SHEET_URL).sheet1
except gspread.exceptions.APIError as e:
    st.error(f"❌ Gagal membuka Google Sheet: {e}")
    st.stop()

# =====================================================
# 📝 APLIKASI STREAMLIT
# =====================================================
st.title("📅 Fitria Content Management")

# --- Header kolom Google Sheets
HEADERS = [
    "No", "Content Pillar", "Platform", "Type of Content", "Status", "Concept",
    "Headline/Hook", "Scripting", "Caption", "Asset", "Time to post", "Date"
]

# --- Opsi dropdown
CONTENT_PILLAR_OPTIONS = ["Education", "Promo", "Tips", "Motivation"]
PLATFORM_OPTIONS = ["Instagram", "TikTok", "Facebook", "YouTube"]
TYPE_CONTENT_OPTIONS = ["Image", "Video", "Reels", "Story"]
STATUS_OPTIONS = ["Draft", "In Progress", "Scheduled", "Posted"]

# =====================================================
# ✍️ FORM INPUT KONTEN
# =====================================================
with st.form("content_form", clear_on_submit=True):
    col1, col2 = st.columns(2)

    # --- Input kiri
    with col1:
        content_pillar = st.selectbox("Content Pillar", CONTENT_PILLAR_OPTIONS)
        platform = st.selectbox("Platform", PLATFORM_OPTIONS)
        type_content = st.selectbox("Type of Content", TYPE_CONTENT_OPTIONS)
        status = st.selectbox("Status", STATUS_OPTIONS)
        concept = st.text_input("Concept")
        headline = st.text_input("Headline/Hook")

    # --- Input kanan
    with col2:
        scripting = st.text_area("Scripting")
        caption = st.text_area("Caption")
        asset = st.text_input("Asset (Link/Folder)")
        time_post_obj = st.time_input("Time to post")
        time_post = time_post_obj.strftime("%H:%M")
        date_post = st.date_input("Date (YYYY-MM-DD)")
        date_post_str = date_post.strftime("%Y-%m-%d")

    # --- Submit button
    submitted = st.form_submit_button("✅ Save to Google Sheets")

    if submitted:
        # Ambil data lama + generate nomor baru
        data = sheet.get_all_records()
        next_no = len(data) + 1

        # Data baru yang akan disimpan
        new_data = [
            next_no, content_pillar, platform, type_content, status, concept,
            headline, scripting, caption, asset, time_post, date_post_str
        ]

        # Simpan ke Google Sheets
        sheet.append_row(new_data)
        st.success("✅ Data berhasil disimpan ke Google Sheets!")

# =====================================================
# 📊 TAMPILKAN DATA
# =====================================================
st.subheader("📊 Data Konten")

data = sheet.get_all_records()
df = pd.DataFrame(data)

if not df.empty:
    st.dataframe(df)
else:
    st.info("Belum ada data konten yang tersimpan.")

# =====================================================
# 📥 EXPORT KE KALENDER (ICS)
# =====================================================
if not df.empty:
    st.subheader("📥 Export ke Calendar (.ics)")

    selected = st.selectbox("Pilih konten untuk export:", df["Headline/Hook"])

    if st.button("📤 Export ICS"):
        # Ambil data berdasarkan headline
        row = df[df["Headline/Hook"] == selected].iloc[0]

        # Buat event ICS
        cal = Calendar()
        event = Event()
        event.name = row["Headline/Hook"]

        # Format date + time
        date_str = str(row["Date"])
        time_str = str(row["Time to post"])

        try:
            dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            event.begin = dt
        except Exception:
            st.error("❌ Format tanggal/jam salah. Pastikan 'Date' = YYYY-MM-DD dan 'Time to post' = HH:MM.")
            st.stop()

        # Tambahkan detail event
        event.description = f"{row['Caption']}\n\nConcept: {row['Concept']}"
        event.url = row["Asset"]
        cal.events.add(event)

        # Simpan ke file ICS
        ics_file = "content_event.ics"
        with open(ics_file, "w") as f:
            f.writelines(cal.serialize_iter())

        # Tombol download
        with open(ics_file, "rb") as f:
            st.download_button(
                label="⬇️ Download ICS",
                data=f,
                file_name="content_event.ics",
                mime="text/calendar"
            )
