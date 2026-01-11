import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
from datetime import datetime
import re

# Sheet configurations with department column names
SHEET_CONFIGS = [
    {
        "name": "MARKUS 2K26 -  CODE ADAPT (Responses)",
        "display_name": "Code Adapt",
        "roll_columns": ["Team Leader Roll no (eg : 23XXX001)", "Team member 1 Roll number (eg:23XXX001)", "Team member 2 Roll number (eg:23XXX001)"],
        "dept_column": "Department"
    },
    {
        "name": "MARKUS Project Presentation 2k26 (Responses)",
        "display_name": "Project Presentation",
        "roll_columns": ["Team Leader Roll no (eg : 23XXX001)", "Team member 1 Roll number (eg:23XXX001)", "Team member 2 Roll number (eg:23XXX001)"],
        "dept_column": "Department"
    },
    {
        "name": "MARKUS Technical Quiz (Responses)",
        "display_name": "Technical Quiz",
        "roll_columns": ["Roll no (eg : 23XXX001)", "Team Member 2 Roll.no  (eg : 23XXX001)"],
        "dept_column": "Department"
    }
]


def get_gspread_client():
    """
    Get authenticated gspread client using credentials.
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    json_env = os.getenv("GOOGLE_CREDENTIALS_JSON")
    
    if json_env:
        print("Using credentials from environment variable...")
        creds_dict = json.loads(json_env)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        json_path = "backend/markus.json"
        if not os.path.exists(json_path):
            print(f"Error: {json_path} not found and GOOGLE_CREDENTIALS_JSON env var not set.")
            return None
        print("Using credentials from local file...")
        creds = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)

    return gspread.authorize(creds)


def normalize_department(dept_value: str) -> str:
    """
    Normalize department names to consistent format.
    """
    if not dept_value or not isinstance(dept_value, str):
        return "Other"
    
    dept = dept_value.strip().upper()
    
    # Map common variations to standard names
    dept_mapping = {
        # MSc departments
        "MSC(IS&R)": "MSc Information Science",
        "MSC (IS&R)": "MSc Information Science",
        "MSC IS&R": "MSc Information Science",
        "MSC-IS&R": "MSc Information Science",
        "ISR": "MSc Information Science",
        "IS&R": "MSc Information Science",
        "MSC(ISR)": "MSc Information Science",
        "MSC IT": "MSc Information Technology",
        "MSC (IT)": "MSc Information Technology",
        "MSC(IT)": "MSc Information Technology",
        "MSC-IT": "MSc Information Technology",
        "MSC SS": "MSc Software Systems",
        "MSC (SS)": "MSc Software Systems",
        "MSC(SS)": "MSc Software Systems",
        "MSC-SS": "MSc Software Systems",
        "MSC CT": "MSc Computer Technology",
        "MSC (CT)": "MSc Computer Technology",
        "MSC(CT)": "MSc Computer Technology",
        "MSC-CT": "MSc Computer Technology",
        "MSC DS": "MSc Data Science",
        "MSC (DS)": "MSc Data Science",
        "MSC(DS)": "MSc Data Science",
        "MSC-DS": "MSc Data Science",
        
        # BSc departments
        "BSC": "BSc",
        "B.SC": "BSc",
        "B.SC.": "BSc",
        "BSC CT": "BSc Computer Technology",
        "BSC(CT)": "BSc Computer Technology",
        "BSC IT": "BSc Information Technology",
        "BSC(IT)": "BSc Information Technology",
        
        # MCA
        "MCA": "MCA",
        "M.C.A": "MCA",
        "M.C.A.": "MCA",
        
        # Engineering departments - CSE
        "CSE": "Computer Science",
        "COMPUTER SCIENCE": "Computer Science",
        "COMPUTER SCIENCE AND ENGINEERING": "Computer Science",
        "CSD": "Computer Science & Design",
        "CSBS": "Computer Science & Business Systems",
        
        # Electronics
        "ECE": "Electronics & Communication",
        "ELECTRONICS": "Electronics & Communication",
        "ELECTRONICS AND COMMUNICATION": "Electronics & Communication",
        "EIE": "Electronics & Instrumentation",
        "ELECTRONICS AND INSTRUMENTATION": "Electronics & Instrumentation",
        
        # Electrical
        "EEE": "Electrical Engineering",
        "ELECTRICAL": "Electrical Engineering",
        "ELECTRICAL AND ELECTRONICS": "Electrical Engineering",
        
        # Mechanical & related
        "MECH": "Mechanical",
        "MECHANICAL": "Mechanical",
        "MECHANICAL ENGINEERING": "Mechanical",
        "AUTO": "Automobile Engineering",
        "AUTOMOBILE": "Automobile Engineering",
        "AUTOMOBILE ENGINEERING": "Automobile Engineering",
        
        # Civil
        "CIVIL": "Civil",
        "CIVIL ENGINEERING": "Civil",
        
        # IT
        "IT": "Information Technology",
        "INFORMATION TECHNOLOGY": "Information Technology",
        
        # AI/ML
        "AI": "Artificial Intelligence",
        "AIDS": "AI & Data Science",
        "AI&DS": "AI & Data Science",
        "AIML": "AI & Machine Learning",
        "AI&ML": "AI & Machine Learning",
        
        # Other
        "CY": "Cyber Security",
        "CYBER": "Cyber Security",
        "CYBER SECURITY": "Cyber Security",
        "MBA": "Business Administration",
        "CHEMICAL": "Chemical Engineering",
        "CHEMICAL ENGINEERING": "Chemical Engineering",
        "FT": "Food Technology",
        "FOOD TECHNOLOGY": "Food Technology",
        "FOOD TECH": "Food Technology",
        "BT": "Biotechnology",
        "BIOTECH": "Biotechnology",
        "BIOTECHNOLOGY": "Biotechnology",
        "TEXTILE": "Textile Technology",
        "TEXTILE TECHNOLOGY": "Textile Technology",
        "FASHION": "Fashion Technology",
        "FASHION TECHNOLOGY": "Fashion Technology",
    }
    
    # Check exact matches first
    if dept in dept_mapping:
        return dept_mapping[dept]
    
    # Check partial matches
    for key, value in dept_mapping.items():
        if key in dept or dept in key:
            return value
    
    # Return original if no match (with proper casing)
    return dept_value.strip().title()


def extract_roll_numbers_from_row(row: dict, roll_columns: list) -> list:
    """
    Extract all roll numbers from a row based on column names.
    Returns a list of normalized (uppercase) roll numbers.
    """
    roll_numbers = []
    
    for col_name in roll_columns:
        if col_name in row:
            value = row[col_name]
            if value and isinstance(value, str) and value.strip():
                # Normalize roll number to uppercase
                roll_no = value.upper().strip()
                if roll_no and len(roll_no) >= 5:  # Basic validation
                    roll_numbers.append(roll_no)
    
    return list(set(roll_numbers))  # Remove duplicates


def extract_department_from_row(row: dict, dept_column: str) -> str:
    """
    Extract department from the row using the specified column.
    """
    if dept_column in row:
        return normalize_department(row[dept_column])
    
    # Try case-insensitive match
    for key in row.keys():
        if key.upper() == dept_column.upper():
            return normalize_department(row[key])
    
    return "Other"


def fetch_admin_analytics():
    """
    Fetch analytics data from all three Google Sheets.
    Returns:
        - total_unique: Count of unique participants
        - total_responses: Total number of responses across all sheets
        - events: List of {name, count} for each event
        - departments: List of {code, name, count, percentage} for department breakdown
        - refresh_time: Timestamp of data fetch
    """
    try:
        client = get_gspread_client()
        if not client:
            return {
                "error": "Could not authenticate with Google Sheets",
                "total_unique": 0,
                "total_responses": 0,
                "events": [],
                "departments": [],
                "dept_count": 0,
                "refresh_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        all_roll_numbers = set()  # For unique participants
        roll_to_dept = {}  # Map roll number to department
        total_responses = 0
        events_data = []
        
        for sheet_config in SHEET_CONFIGS:
            try:
                print(f"📊 Fetching: {sheet_config['name']}...")
                spreadsheet = client.open(sheet_config["name"])
                worksheet = spreadsheet.sheet1
                
                # Get all records
                records = worksheet.get_all_records()
                response_count = len(records)
                total_responses += response_count
                
                events_data.append({
                    "name": sheet_config["display_name"],
                    "count": response_count
                })
                
                # Extract all roll numbers and departments from this sheet
                for record in records:
                    roll_numbers = extract_roll_numbers_from_row(
                        record, 
                        sheet_config["roll_columns"]
                    )
                    dept = extract_department_from_row(record, sheet_config["dept_column"])
                    
                    for roll_no in roll_numbers:
                        all_roll_numbers.add(roll_no)
                        # Store department for this roll number (use first occurrence)
                        if roll_no not in roll_to_dept:
                            roll_to_dept[roll_no] = dept
                
                print(f"   ✅ Found {response_count} responses")
                
            except Exception as e:
                print(f"   ❌ Error fetching {sheet_config['name']}: {e}")
                events_data.append({
                    "name": sheet_config["display_name"],
                    "count": 0
                })

        # Calculate department breakdown from collected data
        dept_counts = {}
        for roll_no in all_roll_numbers:
            dept = roll_to_dept.get(roll_no, "Other")
            dept_counts[dept] = dept_counts.get(dept, 0) + 1
        
        # Calculate percentages and format department data
        total_unique = len(all_roll_numbers)
        departments = []
        
        # Generate color codes for departments
        dept_colors = {
            "MSc Information Science": "isr",
            "MSc Information Technology": "it",
            "MSc Software Systems": "ss",
            "MSc Computer Technology": "ct",
            "MSc Data Science": "ds",
            "BSc": "other",
            "BSc Computer Technology": "ct",
            "BSc Information Technology": "it",
            "MCA": "mca",
            "Computer Science": "cse",
            "Computer Science & Design": "cse",
            "Computer Science & Business Systems": "cse",
            "Electronics & Communication": "ece",
            "Electronics & Instrumentation": "ece",
            "Electrical Engineering": "eee",
            "Mechanical": "mech",
            "Automobile Engineering": "mech",
            "Civil": "civil",
            "Information Technology": "it",
            "Artificial Intelligence": "ai",
            "AI & Data Science": "aids",
            "AI & Machine Learning": "aiml",
            "Cyber Security": "cy",
            "Business Administration": "mba",
            "Chemical Engineering": "other",
            "Food Technology": "other",
            "Biotechnology": "other",
            "Textile Technology": "other",
            "Fashion Technology": "other",
        }
        
        for name, count in sorted(dept_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = round((count / total_unique * 100), 1) if total_unique > 0 else 0
            code = dept_colors.get(name, "other")
            departments.append({
                "code": code,
                "name": name,
                "count": count,
                "percentage": percentage
            })

        return {
            "total_unique": total_unique,
            "total_responses": total_responses,
            "events": events_data,
            "departments": departments,
            "dept_count": len(departments),
            "refresh_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        print(f"❌ Error in fetch_admin_analytics: {e}")
        return {
            "error": str(e),
            "total_unique": 0,
            "total_responses": 0,
            "events": [],
            "departments": [],
            "dept_count": 0,
            "refresh_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


if __name__ == "__main__":
    # Test the analytics function
    result = fetch_admin_analytics()
    print("\n" + "="*50)
    print("📊 ADMIN ANALYTICS RESULTS")
    print("="*50)
    print(f"Total Unique Participants: {result['total_unique']}")
    print(f"Total Responses: {result['total_responses']}")
    print(f"\n🎯 Events:")
    for event in result['events']:
        print(f"   - {event['name']}: {event['count']} responses")
    print(f"\n🏛️ Departments ({result['dept_count']} total):")
    for dept in result['departments']:
        print(f"   - {dept['name']}: {dept['count']} ({dept['percentage']}%)")
