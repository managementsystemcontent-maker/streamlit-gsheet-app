import os
import pandas as pd

# Google Sheets
def _get_gspread_client():
    import gspread
    from google.oauth2.service_account import Credentials
    json_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "service_account.json")
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(json_path, scopes=scopes)
    gc = gspread.authorize(creds)
    return gc

def read_plan(sheet_key: str = None, worksheet_name: str = "Plan", fallback_path: str = "content_plan.xlsx") -> pd.DataFrame:
    sheet_key = sheet_key or os.getenv("GSHEET_ID", "").strip()
    if sheet_key:
        gc = _get_gspread_client()
        sh = gc.open_by_key(sheet_key)
        try:
            ws = sh.worksheet(worksheet_name)
        except Exception:
            ws = sh.sheet1
        df = pd.DataFrame(ws.get_all_records())
        return df
    # If no Google Sheet, raise error instead of fallback
    raise RuntimeError("Google Sheet ID not set. Please set GSHEET_ID in your environment.")

def append_row(row: dict, sheet_key: str = None, worksheet_name: str = "Plan", fallback_path: str = "content_plan.xlsx"):
    sheet_key = sheet_key or os.getenv("GSHEET_ID", "").strip()
    headers = ["No","Content Pillar","Platform","Type of Content","Status","Concept","Headline/Hook","Scripting","Caption","Asset (Link/Folder)","Time to post (HH:MM)","Date"]
    if sheet_key:
        gc = _get_gspread_client()
        sh = gc.open_by_key(sheet_key)
        try:
            ws = sh.worksheet(worksheet_name)
        except Exception:
            ws = sh.sheet1
        # Ensure header exists
        existing = ws.get_all_values()
        if not existing:
            ws.append_row(headers)
        values = [row.get(h, "") for h in headers]
        ws.append_row(values)
        return
    # fallback Excel: append and overwrite
    try:
        df = pd.read_excel(fallback_path)
    except FileNotFoundError:
        df = pd.DataFrame(columns=headers)
    df.loc[len(df)] = [row.get(h, "") for h in headers]
    df.to_excel(fallback_path, index=False)