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
    "UI/UX (Responses)",  # Fixed spacing
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
            spreadsheet = client.open(sheet_name)
            
            # Special handling for UI/UX sheet to target 'Form Responses 1'
            if "UI/UX" in sheet_name:
                try:
                    sheet = spreadsheet.worksheet("Form Responses 1")
                except gspread.WorksheetNotFound:
                    print(f"   ⚠️ 'Form Responses 1' not found in {sheet_name}, falling back to first sheet")
                    sheet = spreadsheet.sheet1
            else:
                sheet = spreadsheet.sheet1
                
            rows = sheet.get_all_values()
            if not rows: continue

            headers = rows[0]
            print(f"   Headers: {headers[:5]}...")  # Debug: show first 5 headers
            
            # Find Column Indices - expanded keywords
            idx_name = find_column(headers, ["name with initial", "name", "student name", "full name", "leader name"])
            idx_roll = find_column(headers, ["roll no", "roll", "reg", "registration", "leader roll"])
            idx_dept = find_column(headers, ["department", "dept", "branch"])
            idx_year = find_column(headers, ["year", "yr", "batch"])
            
            # Find all team member name columns
            team_member_indices = []
            for idx, h in enumerate(headers):
                h_lower = h.lower()
                # Look for team member columns
                if ("team member" in h_lower or "member" in h_lower) and "name" in h_lower:
                    team_member_indices.append(idx)
            
            print(f"   Column indices - Name:{idx_name}, Roll:{idx_roll}, Dept:{idx_dept}, Year:{idx_year}")
            if team_member_indices:
                print(f"   Team member name columns found at indices: {team_member_indices}")
            
            # Process Rows
            count = 0
            for row in rows[1:]:
                # Safely get values
                roll = row[idx_roll].strip().upper() if idx_roll != -1 and idx_roll < len(row) else ""
                
                # Basic validation
                if not roll or len(roll) < 5: continue
                
                name = row[idx_name].strip().upper() if idx_name != -1 and idx_name < len(row) else ""
                dept = row[idx_dept].strip() if idx_dept != -1 and idx_dept < len(row) else ""
                year = row[idx_year].strip() if idx_year != -1 and idx_year < len(row) else ""
                
                # Extract team member names
                team_members_list = []
                for tm_idx in team_member_indices:
                    if tm_idx < len(row) and row[tm_idx].strip():
                        team_members_list.append(row[tm_idx].strip())
                
                # Join team members with comma separator
                team_members = ", ".join(team_members_list) if team_members_list else None
                
                # Fallback Year extraction from Roll
                if not year:
                    if roll.startswith("25"): year = "I"
                    elif roll.startswith("24"): year = "II"
                    elif roll.startswith("23"): year = "III"
                    elif roll.startswith("22"): year = "IV"
                
                save_participant(roll, name, dept, year, sheet_name, sheet_name, team_members)
                count += 1
            print(f"   ✅ Saved {count} records.")

        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    sync_data()
