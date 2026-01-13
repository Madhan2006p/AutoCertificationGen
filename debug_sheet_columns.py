import gspread
from google.oauth2.service_account import Credentials
import os
import json

def debug_sheet_columns():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    json_env = os.getenv("GOOGLE_CREDENTIALS_JSON")
    
    if json_env:
        creds_dict = json.loads(json_env)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    else:
        json_path = "backend/markus.json"
        creds = Credentials.from_service_account_file(json_path, scopes=scope)

    client = gspread.authorize(creds)

    sheets_to_check = [
        "CHILL & SKILL (Responses)",
        "UI/UX  (Responses)"
    ]

    with open("sheet_columns.txt", "w", encoding="utf-8") as f:
        for sheet_name in sheets_to_check:
            f.write(f"\n{'='*60}\n")
            f.write(f"Sheet: {sheet_name}\n")
            f.write('='*60 + "\n")
            
            try:
                spreadsheet = client.open(sheet_name)
                worksheet = spreadsheet.sheet1
                headers = worksheet.row_values(1)
                
                f.write(f"\nFound {len(headers)} columns:\n")
                for i, header in enumerate(headers, 1):
                    f.write(f"{i}. '{header}'\n")
                
                if len(worksheet.get_all_values()) > 1:
                    first_row = worksheet.row_values(2)
                    f.write(f"\nSample data (first row):\n")
                    for i, (header, value) in enumerate(zip(headers, first_row), 1):
                        if value and 'roll' in header.lower():
                            f.write(f"{i}. {header}: '{value}'\n")
                            
            except Exception as e:
                f.write(f"ERROR: {e}\n")
    
    print("Column information saved to sheet_columns.txt")

if __name__ == "__main__":
    debug_sheet_columns()
