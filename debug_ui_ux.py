
import sys
import os
import gspread
from google.oauth2.service_account import Credentials
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_ui_ux():
    print("🔍 Debugging 'UI/UX (Responses)' sheet access...")
    
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    json_path = os.path.join(os.path.dirname(__file__), "backend", "markus.json")
    
    if not os.path.exists(json_path):
        print(f"❌ Credentials file not found at {json_path}")
        return

    try:
        creds = Credentials.from_service_account_file(json_path, scopes=scope)
        client = gspread.authorize(creds)
        print("✅ Authenticated with Google.")
        
        print("\n🔍 Listing all available spreadsheets:")
        for ss in client.openall():
            print(f"   - '{ss.title}'")

        sheet_name = "UI/UX (Responses)"

        print(f"   Opening spreadsheet: '{sheet_name}'")
        
        try:
            spreadsheet = client.open(sheet_name)
            print("   ✅ Spreadsheet opened successfully.")
            
            # List all worksheets
            worksheets = spreadsheet.worksheets()
            print("\n   📋 Available Worksheets:")
            for ws in worksheets:
                print(f"      - '{ws.title}' (ID: {ws.id})")
            
            target_ws_name = "Form Responses 1"
            print(f"\n   Trying to access: '{target_ws_name}'")
            
            try:
                sheet = spreadsheet.worksheet(target_ws_name)
                print("   ✅ Worksheet found!")
                
                rows = sheet.get_all_values()
                print(f"   ✅ Fetched {len(rows)} rows.")
                if len(rows) > 0:
                    print(f"   Headers: {rows[0]}")
                
            except gspread.WorksheetNotFound:
                print(f"   ❌ Worksheet '{target_ws_name}' NOT FOUND.")
                
        except Exception as e:
            print(f"   ❌ Error opening spreadsheet: {e}")

    except Exception as e:
        print(f"   ❌ Auth Error: {e}")

if __name__ == "__main__":
    debug_ui_ux()
