import streamlit as st
import gspread
import pandas as pd
from datetime import datetime, time
from ics import Calendar, Event

# --- SETUP GOOGLE SHEETS ---
try:
    # Menggunakan st.secrets untuk kredensial yang lebih aman di Streamlit Cloud
    creds = st.secrets["gcp_service_account"]
    
    # Lingkup akses yang diperlukan
    scope = ["https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive"]
    
    # Otorisasi gspread client dengan kredensial dari st.secrets
    client = gspread.service_account_from_dict(creds, scopes=scope)

except Exception as e:
    st.error(f"Gagal memuat kredensial dari st.secrets: {e}")
    st.info("Pastikan Anda sudah menambahkan kredensial di Streamlit Secrets.")
    st.stop() # Hentikan eksekusi jika kredensial gagal

# Buka Google Sheet (ganti URL/ID sesuai sheet lo)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1IVzpOG7R7YD4F3geE06rbb8ouLwkeC53RUQPhUlbR-4/edit"
try:
    sheet = client.open_by_url(SHEET_URL).sheet1
except gspread.exceptions.APIError as e:
    st.error(f"Gagal membuka Google Sheet: {e}")
    st.stop()

st.title("📅 Fitria Content Management")

# --- KELOMPOK INPUT DAN OPSIONAL ---
headers = [
    "No", "Content Pillar", "Platform", "Type of Content", "Status", "Concept",
    "Headline/Hook", "Scripting", "Caption", "Asset", "Time to post", "Date"
]

# Opsi dropdown (edit sesuai kebutuhan)
content_pillar_options = ["Education", "Promo", "Tips", "Motivation"]
platform_options = ["Instagram", "TikTok", "Facebook", "YouTube"]
type_content_options = ["Image", "Video", "Reels", "Story"]
status_options = ["Draft", "In Progress", "Scheduled", "Posted"]

# --- INPUT FORM ---
with st.form("content_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        content_pillar = st.selectbox("Content Pillar", content_pillar_options)
        platform = st.selectbox("Platform", platform_options)
        type_content = st.selectbox("Type of Content", type_content_options)
        status = st.selectbox("Status", status_options)
        concept = st.text_input("Concept")
        headline = st.text_input("Headline/Hook")
    with col2:
        scripting = st.text_area("Scripting")
        caption = st.text_area("Caption")
        asset = st.text_input("Asset (Link/Folder)")
        # Menggunakan st.time_input untuk input jam yang lebih baik
        time_post_obj = st.time_input("Time to post") 
        time_post = time_post_obj.strftime("%H:%M")
        date_post = st.date_input("Date (YYYY-MM-DD)")
        date_post_str = date_post.strftime("%Y-%m-%d")

    submitted = st.form_submit_button("✅ Save to Google Sheets")

    if submitted:
        data = sheet.get_all_records()
        next_no = len(data) + 1
        new_data = [
            next_no, content_pillar, platform, type_content, status, concept,
            headline, scripting, caption, asset, time_post, date_post_str
        ]
        sheet.append_row(new_data)
        st.success("Data berhasil disimpan ke Google Sheets ✅")

# --- TAMPILKAN DATA ---
st.subheader("📊 Data Konten")
data = sheet.get_all_records()
df = pd.DataFrame(data)
st.dataframe(df)

# --- EXPORT ICS ---
if not df.empty:
    st.subheader("📥 Export ke Calendar (.ics)")
    selected = st.selectbox("Pilih konten untuk export:", df["Headline/Hook"])

    if st.button("Export ICS"):
        row = df[df["Headline/Hook"] == selected].iloc[0]
        cal = Calendar()
        event = Event()
        event.name = row["Headline/Hook"]

        # Format date and time untuk ICS
        date_str = str(row["Date"])
        time_str = str(row["Time to post"])
        try:
            dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            # ICS menggunakan format datetime yang spesifik
            event.begin = dt
        except Exception:
            st.error("Format tanggal atau jam salah. Pastikan 'Date' = YYY-MM-DD dan 'Time to post' = HH:MM.")
            st.stop()

        event.description = f"{row['Caption']}\n\nConcept: {row['Concept']}"
        event.url = row["Asset"]
        cal.events.add(event)

        ics_file = "content_event.ics"
        with open(ics_file, "w") as f:
            f.writelines(cal.serialize_iter())

        with open(ics_file, "rb") as f:
            st.download_button(
                label="Download ICS",
                data=f,
                file_name="content_event.ics",
                mime="text/calendar"
            )
