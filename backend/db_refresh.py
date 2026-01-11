import sqlite3
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

def refresh():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    # Try environment variable first (for Render deployment)
    # Then fall back to local file (for local development)
    json_env = os.getenv("GOOGLE_CREDENTIALS_JSON")
    
    if json_env:
        # Parse JSON from environment variable
        print("Using credentials from environment variable...")
        creds_dict = json.loads(json_env)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        # Fall back to local file
        json_path = "backend/markus.json"
        if not os.path.exists(json_path):
            print(f"Error: {json_path} not found and GOOGLE_CREDENTIALS_JSON env var not set.")
            return
        print("Using credentials from local file...")
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
    
    # --- PRESERVE CERT URLS ---
    try:
        existing_urls = pd.read_sql_query("SELECT roll_no, event, cert_url FROM participants", conn)
        df_final = pd.merge(df_clean, existing_urls, on=["roll_no", "event"], how="left")
    except Exception:
        df_final = df_clean
        df_final["cert_url"] = None

    df_final.to_sql(
        name="participants",
        con=conn,
        if_exists="replace",
        index=False
    )

    # Add 'generating' column for race condition protection
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE participants ADD COLUMN generating INTEGER DEFAULT 0")
        conn.commit()
        print("✅ Added 'generating' column.")
    except sqlite3.OperationalError:
        pass  # Column already exists

    conn.close()
    print(f"✅ Synced {len(df_final)} participant-event records. cert_urls preserved.")

if __name__ == "__main__":
    refresh()
