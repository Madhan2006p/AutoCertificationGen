import sqlite3
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials


scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    "markus.json" , scope
)

client = gspread.authorize(creds)


SHEET_NAME = "TALENT SHOW -QUANTUM FEST 2K25 (Responses)"


sheet = client.open(SHEET_NAME).sheet1


data = sheet.get_all_records()

df = pd.DataFrame(data)

print("Fetched Rows: ", len(df))

conn = sqlite3.connect("forms_data.db")


df.to_sql(
    name = "form_responses" ,
    con = conn ,
    if_exists="replace",
    index = False
)

conn.close()

print(" Data has Been Saved Successfully.")