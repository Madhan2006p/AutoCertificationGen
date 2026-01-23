import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import os
import json
import re
from backend.database import save_participant, init_db

# Sheet Configs
SHEETS = [
    "MARKUS 2K26 -  CODE ADAPT (Responses)",
    "MARKUS Project Presentation 2k26 (Responses)",
    "MARKUS Technical Quiz (Responses)",
    "CHILL & SKILL (Responses)",
    "UI/UX  (Responses)",
    "Paper (Responses)" # Adjusted assumption
]

def get_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    # Check env var first (Render)
    json_env = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if json_env:
        creds_dict = json.loads(json_env)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    else:
        # Local file
        json_path = os.path.join(os.path.dirname(__file__), "markus.json")
        if not os.path.exists(json_path):
            print("❌ DB Sync Error: Credentials not found.")
            return None
        creds = Credentials.from_service_account_file(json_path, scopes=scope)
    
    return gspread.authorize(creds)

def find_column(headers, keywords):
    """Smart search for column index"""
    for idx, h in enumerate(headers):
        h_lower = h.lower()
        for k in keywords:
            if k in h_lower:
                return idx
    return -1

def sync_data():
    print("🔄 Syncing Data...")
    init_db()
    client = get_client()
    if not client: return

    for sheet_name in SHEETS:
        print(f"📊 Processing: {sheet_name}")
        try:
            sheet = client.open(sheet_name).sheet1
            rows = sheet.get_all_values()
            if not rows: continue

            headers = rows[0]
            print(f"   Headers: {headers[:5]}...")  # Debug: show first 5 headers
            
            # Find Column Indices - expanded keywords
            idx_name = find_column(headers, ["name with initial", "name", "student name", "full name", "leader name"])
            idx_roll = find_column(headers, ["roll no", "roll", "reg", "registration", "leader roll"])
            idx_dept = find_column(headers, ["department", "dept", "branch"])
            idx_year = find_column(headers, ["year", "yr", "batch"])
            
            print(f"   Column indices - Name:{idx_name}, Roll:{idx_roll}, Dept:{idx_dept}, Year:{idx_year}")
            
            # Process Rows
            count = 0
            for row in rows[1:]:
                # Safely get values
                roll = row[idx_roll].strip().upper() if idx_roll != -1 and idx_roll < len(row) else ""
                
                # Specialized logic for team members?
                # The user said "Search the coloumn".
                # If there are multiple fields (Team member 1, 2), a simple linear search might miss them.
                # However, for the MVP "Fetch... Name, Dept, Year", looking for the PRIMARY columns is safest.
                # If the user wants ALL team members, we'd need to iterate header patterns.
                # Let's assume standard single-entry for now or primary leader.
                # Use a specific logic if roll is empty?
                
                # Basic validation
                if not roll or len(roll) < 5: continue
                
                name = row[idx_name].strip().upper() if idx_name != -1 and idx_name < len(row) else ""
                dept = row[idx_dept].strip() if idx_dept != -1 and idx_dept < len(row) else ""
                year = row[idx_year].strip() if idx_year != -1 and idx_year < len(row) else ""
                
                # Fallback Year extraction from Roll
                if not year:
                    if roll.startswith("25"): year = "I"
                    elif roll.startswith("24"): year = "II"
                    elif roll.startswith("23"): year = "III"
                    elif roll.startswith("22"): year = "IV"
                
                save_participant(roll, name, dept, year, sheet_name, sheet_name)
                count += 1
            print(f"   ✅ Saved {count} records.")

        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    sync_data()
