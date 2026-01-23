import sqlite3
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import os
import json
import sys

# Import config from admin_analytics
try:
    from admin_analytics import get_gspread_client, SHEET_CONFIGS, normalize_department
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from admin_analytics import get_gspread_client, SHEET_CONFIGS, normalize_department

def get_year_from_roll(roll_no):
    """
    Calculate year based on roll number prefix.
    """
    if not roll_no or len(roll_no) < 2:
        return ""
    try:
        prefix = roll_no[:2]
        if prefix.isdigit():
            val = int(prefix)
            if val == 25: return "I"
            if val == 24: return "II"
            if val == 23: return "III"
            if val == 22: return "IV"
            if val == 21: return "IV+" 
    except:
        pass
    return ""

def find_best_name_column(record, roll_col_name):
    """
    Find the corresponding name column for a given roll number column.
    Same logic as in generate_participation.py
    """
    headers = list(record.keys())
    
    roll_lower = roll_col_name.lower()
    
    # Specific mappings
    if "leader" in roll_lower:
        for h in headers:
            if "leader" in h.lower() and "name" in h.lower() and h != roll_col_name: return h
    if "team member 1" in roll_lower or "member 1" in roll_lower:
        for h in headers:
            if "member 1" in h.lower() and "name" in h.lower() and h != roll_col_name: return h
    if "team member 2" in roll_lower or "member 2" in roll_lower:
        for h in headers:
            if "member 2" in h.lower() and "name" in h.lower() and h != roll_col_name: return h
    
    # Generic mappings
    priority_names = ["Name with initial (eg:Anu A)", "Name", "Student Name", "Full Name"]
    for p in priority_names:
        if p in headers: return p
            
    for h in headers:
        if "name" in h.lower() and "team" not in h.lower() and "file" not in h.lower(): return h
    return None

def refresh():
    print("🔄 Starting DB Sync from Event Sheets...")
    client = get_gspread_client()
    if not client:
        print("❌ Authentication failed")
        return

    all_participants = []

    for config in SHEET_CONFIGS:
        print(f"📊 Fetching: {config['display_name']}...")
        try:
            sheet = client.open(config["name"]).sheet1
            
            # Safe data extraction (handling duplicate headers)
            headers = sheet.row_values(1)
            all_values = sheet.get_all_values()
            
            cleaned_headers = []
            empty_count = 0
            for h in headers:
                if not h.strip():
                    empty_count += 1
                    cleaned_headers.append(f"empty_{empty_count}")
                else:
                    cleaned_headers.append(h)
            
            records = []
            for row in all_values[1:]:
                if any(row):
                    rec = {}
                    for i, val in enumerate(row):
                        if i < len(cleaned_headers):
                            rec[cleaned_headers[i]] = val
                    records.append(rec)
            
            # Extract participants
            count = 0
            for record in records:
                for roll_col in config["roll_columns"]:
                    roll_no = record.get(roll_col, "").strip().upper()
                    if not roll_no or len(roll_no) < 5:
                        continue
                        
                    name_col = find_best_name_column(record, roll_col)
                    name = record.get(name_col, "").strip().upper() if name_col else ""
                    
                    if not name:
                        continue # Skip if name not found in form
                        
                    all_participants.append({
                        "roll_no": roll_no.lower(), # Store as lowercase for consistency
                        "name": name,
                        "year": get_year_from_roll(roll_no),
                        "event": config["display_name"]
                    })
                    count += 1
            print(f"   ✅ Found {count} participants")
            
        except Exception as e:
            print(f"   ❌ Error processing {config['name']}: {e}")

    # Create DataFrame
    df_new = pd.DataFrame(all_participants)
    
    if df_new.empty:
        print("⚠️ No participants found across all sheets.")
        return

    # Remove duplicates (same person, same event)
    df_new = df_new.drop_duplicates(subset=["roll_no", "event"])
    
    conn = sqlite3.connect("forms_data.db")
    
    # --- PRESERVE CERT URLS & GENERATING STATUS ---
    try:
        existing_data = pd.read_sql_query("SELECT roll_no, event, cert_url, generating FROM participants", conn)
        # Merge to keep existing cert_url and generating flag
        df_final = pd.merge(df_new, existing_data, on=["roll_no", "event"], how="left")
        
        # Fill NaN for new records
        df_final["generating"] = df_final["generating"].fillna(0).astype(int)
    except Exception:
        print("   ℹ️ Creating new table structure")
        df_final = df_new
        df_final["cert_url"] = None
        df_final["generating"] = 0

    # Save to SQLite
    df_final.to_sql(
        name="participants",
        con=conn,
        if_exists="replace",
        index=False
    )
    
    conn.close()
    print(f"✅ Sync Complete. Total records: {len(df_final)}")

if __name__ == "__main__":
    refresh()
