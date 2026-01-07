import sqlite3
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import os

def refresh():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    # Use environment variable for JSON key if available, else fallback
    json_path = "backend/markus.json"
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found.")
        return

    creds = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)
    client = gspread.authorize(creds)

    SHEET_NAME = "QuantumFinalList"
    try:
        sheet = client.open(SHEET_NAME).sheet1
    except Exception as e:
        print(f"Error opening sheet: {e}")
        return

    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    if df.empty:
        print("Sheet is empty.")
        return

    # Clean columns
    df.columns = (
        pd.Index(df.columns)
        .astype(str)
        .str.strip()
        .str.replace("\n", " ", regex=False)
        .str.upper()
    )

    df_clean = df[[
        "ROLL NO",
        "NAME",
        "YEAR",
        "EVENTS"
    ]].copy()

    df_clean.columns = ["roll_no", "name", "year", "event"]
    df_clean["roll_no"] = df_clean["roll_no"].str.lower()
    df_clean["event"] = df_clean["event"].str.split(",")
    df_clean = df_clean.explode("event")
    df_clean["event"] = df_clean["event"].str.strip()
    df_clean = df_clean[df_clean["event"] != ""]

    conn = sqlite3.connect("forms_data.db")
    
    # --- PRESERVE CERTURLS ---
    try:
        existing_urls = pd.read_sql_query("SELECT roll_no, event, cert_url FROM participants", conn)
        # Merge new data with existing urls
        df_final = pd.merge(df_clean, existing_urls, on=["roll_no", "event"], how="left")
    except Exception:
        # Table doesn't exist yet
        df_final = df_clean
        df_final["cert_url"] = None

    df_final.to_sql(
        name="participants",
        con=conn,
        if_exists="replace",
        index=False
    )

    conn.close()
    print(f"✅ Synced {len(df_final)} participant-event records. cert_urls preserved.")

if __name__ == "__main__":
    refresh()
