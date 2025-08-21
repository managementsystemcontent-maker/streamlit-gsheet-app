# -*- coding: utf-8 -*-
import os
from datetime import datetime

import gspread
import pandas as pd
import streamlit as st
from ics import Calendar, Event

# =========================
# 🔧 KONFIGURASI
# =========================
SHEET_URL = "https://docs.google.com/spreadsheets/d/1IVzpOG7R7YD4F3geE06rbb8ouLwkeC53RUQPhUlbR-4/edit"

HEADERS = [
    "No", "Content Pillar", "Platform", "Type of Content", "Status", "Concept",
    "Headline/Hook", "Scripting", "Caption", "Asset", "Time to post", "Date"
]

CONTENT_PILLAR_OPTIONS = ["Education", "Promo", "Tips", "Motivation"]
PLATFORM_OPTIONS = ["Instagram", "TikTok", "Facebook", "YouTube"]
TYPE_CONTENT_OPTIONS = ["Image", "Video", "Reels", "Story"]
STATUS_OPTIONS = ["Draft", "In Progress", "Scheduled", "Posted"]

# =========================
# 🧠 OPENROUTER (AI BRAINSTORM)
# =========================
try:
    import openai
    openai.api_key = st.secrets["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"]
    openai.api_base = "https://openrouter.ai/api/v1"
    OPENROUTER_READY = True
except Exception:
    OPENROUTER_READY = False

def ai_brainstorm(user_prompt: str, vibe: str) -> str:
    """Panggil OpenRouter untuk brainstorming ide konten."""
    if not OPENROUTER_READY:
        return "⚠️ OpenRouter belum dikonfigurasi. Tambahkan `openrouter_api_key` di `st.secrets`."
    try:
        resp = openai.ChatCompletion.create(
            model="openrouter/anthropic/claude-3.5-sonnet",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Kamu adalah asisten kreatif berbahasa Indonesia yang membantu brainstorming ide konten "
                        "untuk Instagram/TikTok/Facebook/YouTube. Jawab dengan poin-poin rapi, berikan variasi angle, "
                        "ide hook, CTA, dan contoh caption singkat. Gaya fun, suportif, dan sedikit gemesin 💕."
                    ),
                },
                {"role": "user", "content": f"Gaya: {vibe}\n\n{user_prompt}"},
            ],
            temperature=0.8,
        )
        return resp["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ Gagal memanggil AI: {e}"

# =========================
# 📗 GOOGLE SHEETS
# =========================
def get_sheet():
    try:
        creds = st.secrets["gcp_service_account"]
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        client = gspread.service_account_from_dict(creds, scopes=scope)
        ws = client.open_by_url(SHEET_URL).sheet1
        return ws
    except Exception as e:
        st.error(f"❌ Gagal mengakses Google Sheet: {e}")
        st.stop()

def ensure_headers(ws):
    try:
        if not ws.row_values(1):
            ws.insert_row(HEADERS, 1)
    except Exception:
        pass

# =========================
# 🌸 UI SETUP
# =========================
st.set_page_config(page_title="Fitria Content Management", page_icon="🌸", layout="wide")
st.title("🌸💖 Fitria’s Content Buddy & Planner 💖🌸")

# Tab layout
tab_chat, tab_form, tab_data = st.tabs(
    ["🤖 Brainstorming", "📝 Form Konten", "📊 Data & Calendar"]
)

# Load Google Sheets
ws = get_sheet()
ensure_headers(ws)

# =========================
# 🤖 TAB: BRAINSTORMING
# =========================
with tab_chat:
    st.subheader("✨ Yuk brainstorm ide konten dulu ✨")
    st.markdown("Tulis topikmu, aku bantu ide hook, angle, CTA, dan contoh caption. 💌")

    if "last_idea" not in st.session_state:
        st.session_state.last_idea = ""

    colA, colB = st.columns([3, 1])
    with colA:
        prompt = st.text_area(
            "💌 Ceritain topik yang mau dibuat kontennya:",
            placeholder="Misalnya: promo kelas edukasi minggu depan untuk Instagram Reels...",
            height=120,
        )
    with colB:
        vibe = st.selectbox("🎀 Style", ["Aesthetic", "Fun", "Informative", "Persuasive"], index=1)

    if st.button("🌈✨ Generate Ide Lucu ✨🌈"):
        if not prompt.strip():
            st.warning("⚠️ Tulis dulu topiknya, cantik 💕")
        else:
            with st.spinner("⏳ Lagi mikirin ide kreatif buat kamu... 🎀"):
                idea = ai_brainstorm(prompt.strip(), vibe)
            st.session_state.last_idea = idea
            st.success("🎉 Yay! Ini beberapa ide buat kamu 💡✨")
            st.markdown(st.session_state.last_idea)

    if st.session_state.last_idea:
        if st.button("💘 Gunakan hasil ini untuk isi form"):
            st.session_state.prefill_concept = "Ringkasan ide AI (edit sesuai kebutuhan)"
            st.session_state.prefill_caption = st.session_state.last_idea[:1500]
            st.toast("Hasil brainstorming dikirim ke Form Konten 💌", icon="💖")

# =========================
# 📝 TAB: FORM KONTEN
# =========================
with tab_form:
    st.subheader("📝 Simpan Konten ke Google Sheets")

    with st.form("content_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            content_pillar = st.selectbox("Content Pillar", CONTENT_PILLAR_OPTIONS)
            platform = st.selectbox("Platform", PLATFORM_OPTIONS)
            type_content = st.selectbox("Type of Content", TYPE_CONTENT_OPTIONS)
            status = st.selectbox("Status", STATUS_OPTIONS)
            concept = st.text_input("Concept", value=st.session_state.get("prefill_concept", ""))
            headline = st.text_input("Headline/Hook")

        with col2:
            scripting = st.text_area("Scripting")
            caption = st.text_area("Caption", value=st.session_state.get("prefill_caption", ""), height=180)
            asset = st.text_input("Asset (Link/Folder)")
            time_post_obj = st.time_input("Time to post")
            date_post = st.date_input("Date (YYYY-MM-DD)")

        # Format waktu & tanggal
        time_post = time_post_obj.strftime("%H:%M")
        date_post_str = date_post.strftime("%Y-%m-%d")

        submit = st.form_submit_button("✅ Save to Google Sheets")

        if submit:
            try:
                existing = ws.get_all_records()
                next_no = len(existing) + 1
                new_row = [
                    next_no, content_pillar, platform, type_content, status, concept,
                    headline, scripting, caption, asset, time_post, date_post_str
                ]
                ws.append_row(new_row)
                st.success("✅ Data berhasil disimpan ke Google Sheets!")
                st.session_state.prefill_concept = ""
                st.session_state.prefill_caption = ""
            except Exception as e:
                st.error(f"❌ Gagal menyimpan ke Google Sheets: {e}")

# =========================
# 📊 TAB: DATA & CALENDAR
# =========================
with tab_data:
    st.subheader("📊 Data Konten")
    try:
        df = pd.DataFrame(ws.get_all_records())
    except Exception as e:
        df = pd.DataFrame()
        st.error(f"❌ Gagal mengambil data: {e}")

    if df.empty:
        st.info("Belum ada data konten yang tersimpan.")
    else:
        st.dataframe(df, use_container_width=True)

        st.markdown("---")
        st.subheader("📥 Export ke Calendar (.ics)")
        selected = st.selectbox("Pilih konten untuk export:", df["Headline/Hook"])

        if st.button("📤 Export ICS"):
            row = df[df["Headline/Hook"] == selected].iloc[0]
            cal = Calendar()
            event = Event()
            event.name = row["Headline/Hook"]

            try:
                dt = datetime.strptime(f"{row['Date']} {row['Time to post']}", "%Y-%m-%d %H:%M")
                event.begin = dt
            except Exception:
                st.error("❌ Format tanggal/jam salah. Pastikan benar.")
                st.stop()

            event.description = f"{row['Caption']}\n\nConcept: {row['Concept']}"
            event.url = row["Asset"]
            cal.events.add(event)

            with open("content_event.ics", "w", encoding="utf-8") as f:
                f.writelines(cal.serialize_iter())
            with open("content_event.ics", "rb") as f:
                st.download_button("⬇️ Download ICS", f, "content_event.ics", "text/calendar")

# =========================
# 📌 CATATAN
# =========================
st.caption("Requirements: `streamlit`, `gspread`, `pandas`, `ics`, `openai`.\nTambahkan `gcp_service_account` & `openrouter_api_key` di `st.secrets`.")
