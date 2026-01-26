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
    "Paper (Responses)", # Adjusted assumption
    "Markus 2k26 - IPL AUCTION (Responses)"
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


# Mapping for prettier certificate event names
EVENT_MAPPING = {
    "MARKUS 2K26 -  CODE ADAPT (Responses)": "CODE ADAPT",
    "MARKUS Project Presentation 2k26 (Responses)": "PROJECT PRESENTATION",
    "MARKUS Technical Quiz (Responses)": "TECHNICAL QUIZ",
    "CHILL & SKILL (Responses)": "CHILL & SKILL",
    "UI/UX (Responses)": "UI/UX",
    "Paper (Responses)": "PAPER PRESENTATION",
    "Markus 2k26 - IPL AUCTION (Responses)": "IPL AUCTION"
}

def sync_data():
    print("🔄 Syncing Data...")
    init_db()
    client = get_client()
    if not client: return

    for sheet_name in SHEETS:
        print(f"📊 Processing: {sheet_name}")
        # Determine pretty event name
        event_name = EVENT_MAPPING.get(sheet_name, sheet_name.replace(" (Responses)", "").replace("Markus 2k26 - ", "").strip())
        
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
            
            # Find team member columns (paired name and roll columns)
            # Look for patterns like "Team Member 1 Name", "Team Member 1 Roll No"
            team_member_cols = []  # List of (name_idx, roll_idx) tuples
            
            for idx, h in enumerate(headers):
                h_lower = h.lower()
                # Match patterns like "team member 1", "member 1", etc.
                match = re.search(r'(?:team\s*)?member\s*(\d+)', h_lower)
                if match:
                    member_num = match.group(1)
                    if 'name' in h_lower:
                        # Find corresponding roll column for this member number
                        roll_idx = -1
                        for idx2, h2 in enumerate(headers):
                            h2_lower = h2.lower()
                            # Check for "team member X" or "member X" paired with roll/reg
                            if f'member {member_num}' in h2_lower.replace('  ', ' ') and ('roll' in h2_lower or 'reg' in h2_lower):
                                roll_idx = idx2
                                break
                            # Regex fallback
                            if re.search(rf'(?:team\s*)?member\s*{member_num}', h2_lower) and ('roll' in h2_lower or 'reg' in h2_lower):
                                roll_idx = idx2
                                break
                        team_member_cols.append((idx, roll_idx, member_num))
            
            # Sort by member number
            team_member_cols.sort(key=lambda x: int(x[2]))
            
            print(f"   Column indices - Name:{idx_name}, Roll:{idx_roll}, Dept:{idx_dept}, Year:{idx_year}")
            if team_member_cols:
                print(f"   Team member columns: {[(f'Name:{n}, Roll:{r}') for n, r, _ in team_member_cols]}")
            
            # Process Rows
            count = 0
            for row in rows[1:]:
                # Safely get leader values
                leader_roll = row[idx_roll].strip().upper() if idx_roll != -1 and idx_roll < len(row) else ""
                
                # Basic validation for leader
                if not leader_roll or len(leader_roll) < 5: continue
                
                leader_name = row[idx_name].strip().upper() if idx_name != -1 and idx_name < len(row) else ""
                dept = row[idx_dept].strip() if idx_dept != -1 and idx_dept < len(row) else ""
                year = row[idx_year].strip() if idx_year != -1 and idx_year < len(row) else ""
                
                # Fallback Year extraction from Roll
                if not year:
                    if leader_roll.startswith("25"): year = "I"
                    elif leader_roll.startswith("24"): year = "II"
                    elif leader_roll.startswith("23"): year = "III"
                    elif leader_roll.startswith("22"): year = "IV"
                
                # Extract team members with individual roll numbers
                team_members_data = []  # List of {name, roll_no} dicts
                processed_rolls = set()  # Track rolls to prevent duplicates
                processed_rolls.add(leader_roll)  # Leader's roll is already used
                
                for name_idx, roll_idx, member_num in team_member_cols:
                    member_name = row[name_idx].strip() if name_idx < len(row) else ""
                    member_roll = ""
                    if roll_idx != -1 and roll_idx < len(row):
                        member_roll = row[roll_idx].strip().upper()
                    
                    # Skip if no name OR no roll number (as per requirements)
                    if not member_name or not member_roll:
                        continue
                    
                    # Skip if roll number is too short (invalid)
                    if len(member_roll) < 5:
                        continue
                    
                    # Skip duplicate roll numbers (one certificate per roll)
                    if member_roll in processed_rolls:
                        print(f"   ⚠️ Skipping duplicate roll: {member_roll}")
                        continue
                    
                    processed_rolls.add(member_roll)
                    team_members_data.append({
                        "name": member_name,
                        "roll_no": member_roll
                    })
                
                # Save leader and team members
                save_participant(leader_roll, leader_name, dept, year, event_name, sheet_name, team_members_data)
                count += 1
            print(f"   ✅ Saved {count} records.")

        except Exception as e:
            print(f"   ❌ Error processing {sheet_name}: {e}")

if __name__ == "__main__":
    sync_data()
