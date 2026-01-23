import gspread
from google.oauth2.service_account import Credentials
import os
import json

def test_ui_ux_sheet_names():
    """Test different UI/UX sheet name variations to find the correct one."""
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    json_env = os.getenv("GOOGLE_CREDENTIALS_JSON")
    
    if json_env:
        print("Using credentials from environment variable...")
        creds_dict = json.loads(json_env)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    else:
        json_path = "backend/markus.json"
        print("Using credentials from local file...")
        creds = Credentials.from_service_account_file(json_path, scopes=scope)

    client = gspread.authorize(creds)
    
    # Try different variations
    variations = [
        "UI/UX  (Responses)",  # Current (two spaces)
        "UI/UX (Responses)",   # One space
        "Markus 2K25 - UI/UX  (Responses)",  # Old name with spaces
        "Markus 2K25 - UI/UX (Responses)",   # Old name one space
        "MARKUS 2K26 - UI/UX  (Responses)",  # New format two spaces
        "MARKUS 2K26 - UI/UX (Responses)",   # New format one space
        "UI - UX  (Responses)",  # With dashes
        "UI/UX Design (Responses)",
        "MARKUS UI/UX (Responses)",
    ]
    
    print("\n" + "="*60)
    print("Testing UI/UX Sheet Name Variations")
    print("="*60)
    
    for sheet_name in variations:
        try:
            print(f"\n🔍 Trying: '{sheet_name}'")
            spreadsheet = client.open(sheet_name)
            worksheet = spreadsheet.sheet1
            headers = worksheet.row_values(1)
            record_count = len(worksheet.get_all_values()) - 1  # Minus header
            
            print(f"   ✅ SUCCESS! Found {record_count} responses")
            print(f"   Columns: {', '.join(headers[:3])}...")
            print(f"\n🎯 CORRECT SHEET NAME: '{sheet_name}'")
            return sheet_name
            
        except Exception as e:
            error_msg = str(e)
            if "not found" in error_msg.lower():
                print(f"   ❌ Not found")
            else:
                print(f"   ❌ Error: {error_msg[:50]}...")
    
    print("\n❌ None of the variations worked. Please check the exact sheet name in Google Drive.")
    return None

if __name__ == "__main__":
    test_ui_ux_sheet_names()
