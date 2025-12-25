import sqlite3
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

def refresh():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "backend/markus.json", scope
    )
    client = gspread.authorize(creds)


    SHEET_NAME = "QuantumFinalList"
    sheet = client.open(SHEET_NAME).sheet1

    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    print("Fetched Rows:", len(df))

    # 🔥 FIX: Flatten tuple / multi-index columns
    if isinstance(df.columns[0], tuple):
        df.columns = df.columns[0]
    # df.columns == ['S. NO', 'ROLL NO', 'NAME', 'YEAR', 'EVENTS']

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


    df_clean.columns = ["roll_no", "name", "year" ,"event"]

    df_clean["roll_no"] = df_clean["roll_no"].str.lower()
    df_clean["event"] = df_clean["event"].str.split(",")
    

    df_clean = df_clean.explode("event")


    df_clean["event"] = df_clean["event"].str.strip()


    df_clean = df_clean[df_clean["event"] != ""]

    print("Final rows after event split:", len(df_clean))


    conn = sqlite3.connect("forms_data.db")

    df_clean.to_sql(
        name="participants",
        con=conn,
        if_exists="replace",
        index=False
    )

    conn.close()

    print("✅ Roll No, Name, Event saved successfully")
