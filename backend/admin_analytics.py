import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
from datetime import datetime
import re
from collections import defaultdict

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
    },
    {
        "name": "CHILL & SKILL (Responses)",
        "display_name": "Chill & Skill",
        "roll_columns": ["Roll no (eg : 23XXX001)", "Team Member 2 Roll.no  (eg : 23XXX001)", "Team Member 3 Roll.no  (eg : 23XXX001)"],
        "dept_column": "Department"
    },
    {
        "name": "Markus 2K25 - UI/UX  (Responses)",
        "display_name": "UI/UX Design",
        "roll_columns": ["Team Leader Roll no (eg : 23XXX001)", "Team member 1 Roll number (eg:23XXX001)"],
        "dept_column": "Department"
    },
    {
        "name": "Paper (Responses)",
        "display_name": "Paper Presentation",
        "roll_columns": ["Team Leader Roll no (eg : 23XXX001)", "Team member 1 Roll number (eg:23XXX001)"],
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
    Fetch comprehensive analytics data from all three Google Sheets.
    Returns complete analytics for decision making.
    """
    try:
        client = get_gspread_client()
        if not client:
            return get_empty_analytics("Could not authenticate with Google Sheets")

        # Data structures for comprehensive analytics
        roll_to_events = defaultdict(set)  # Track which events each participant joined
        roll_to_dept = {}  # Map roll number to department
        total_responses = 0
        events_data = []
        event_participants = {}  # Track unique participants per event
        
        for sheet_config in SHEET_CONFIGS:
            try:
                print(f"📊 Fetching: {sheet_config['name']}...")
                spreadsheet = client.open(sheet_config["name"])
                worksheet = spreadsheet.sheet1
                
                # Get all records
                records = worksheet.get_all_records()
                response_count = len(records)
                total_responses += response_count
                
                event_name = sheet_config["display_name"]
                event_participants[event_name] = set()
                
                # Extract all roll numbers and departments from this sheet
                for record in records:
                    roll_numbers = extract_roll_numbers_from_row(
                        record, 
                        sheet_config["roll_columns"]
                    )
                    dept = extract_department_from_row(record, sheet_config["dept_column"])
                    
                    for roll_no in roll_numbers:
                        roll_to_events[roll_no].add(event_name)
                        event_participants[event_name].add(roll_no)
                        # Store department for this roll number (use first occurrence)
                        if roll_no not in roll_to_dept:
                            roll_to_dept[roll_no] = dept
                
                events_data.append({
                    "name": event_name,
                    "count": response_count,
                    "unique_participants": len(event_participants[event_name])
                })
                
                print(f"   ✅ Found {response_count} responses, {len(event_participants[event_name])} unique participants")
                
            except Exception as e:
                print(f"   ❌ Error fetching {sheet_config['name']}: {e}")
                events_data.append({
                    "name": sheet_config["display_name"],
                    "count": 0,
                    "unique_participants": 0
                })

        # Calculate participation statistics
        all_roll_numbers = set(roll_to_events.keys())
        total_unique = len(all_roll_numbers)
        
        # Multi-event participation analysis
        single_event = 0
        two_events = 0
        three_events = 0
        four_events = 0
        five_plus_events = 0
        multi_event_participants = []
        
        for roll_no, events in roll_to_events.items():
            event_count = len(events)
            if event_count == 1:
                single_event += 1
            elif event_count == 2:
                two_events += 1
            elif event_count == 3:
                three_events += 1
            elif event_count == 4:
                four_events += 1
            elif event_count >= 5:
                five_plus_events += 1
            
            if event_count >= 2:
                multi_event_participants.append({
                    "roll_no": roll_no,
                    "events": list(events),
                    "event_count": event_count,
                    "dept": roll_to_dept.get(roll_no, "Unknown")
                })
        
        # Sort multi-event participants by event count (descending)
        multi_event_participants.sort(key=lambda x: x["event_count"], reverse=True)
        
        # Calculate department breakdown
        dept_counts = {}
        for roll_no in all_roll_numbers:
            dept = roll_to_dept.get(roll_no, "Other")
            dept_counts[dept] = dept_counts.get(dept, 0) + 1
        
        # Calculate percentages and format department data
        departments = []
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

        # Cross-event analysis (which event combinations are popular)
        event_combinations = defaultdict(int)
        for roll_no, events in roll_to_events.items():
            if len(events) >= 2:
                combo = " + ".join(sorted(events))
                event_combinations[combo] += 1
        
        popular_combos = [
            {"combo": combo, "count": count}
            for combo, count in sorted(event_combinations.items(), key=lambda x: x[1], reverse=True)
        ]

        # Engagement score (average events per participant)
        total_participations = sum(len(events) for events in roll_to_events.values())
        avg_events_per_participant = round(total_participations / total_unique, 2) if total_unique > 0 else 0

        return {
            # Basic stats
            "total_unique": total_unique,
            "total_responses": total_responses,
            "dept_count": len(departments),
            
            # Event data
            "events": events_data,
            
            # Department breakdown
            "departments": departments,
            
            # Multi-event participation
            "participation_breakdown": {
                "single_event": single_event,
                "two_events": two_events,
                "three_events": three_events,
                "four_events": four_events,
                "five_plus_events": five_plus_events,
                "multi_event_total": total_unique - single_event,
                "single_event_pct": round((single_event / total_unique * 100), 1) if total_unique > 0 else 0,
                "multi_event_pct": round(((total_unique - single_event) / total_unique * 100), 1) if total_unique > 0 else 0,
            },
            
            # Top multi-event participants (limit to top 10)
            "multi_event_participants": multi_event_participants[:10],
            
            # Popular event combinations
            "popular_combos": popular_combos,
            
            # Engagement metrics
            "engagement": {
                "avg_events_per_participant": avg_events_per_participant,
                "total_participations": total_participations,
            },
            
            # Metadata
            "refresh_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        print(f"❌ Error in fetch_admin_analytics: {e}")
        return get_empty_analytics(str(e))


def get_empty_analytics(error_msg: str):
    """Return empty analytics structure with error message."""
    return {
        "error": error_msg,
        "total_unique": 0,
        "total_responses": 0,
        "events": [],
        "departments": [],
        "dept_count": 0,
        "participation_breakdown": {
            "single_event": 0,
            "two_events": 0,
            "three_events": 0,
            "multi_event_total": 0,
            "single_event_pct": 0,
            "multi_event_pct": 0,
        },
        "multi_event_participants": [],
        "popular_combos": [],
        "engagement": {
            "avg_events_per_participant": 0,
            "total_participations": 0,
        },
        "refresh_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


if __name__ == "__main__":
    # Test the analytics function
    result = fetch_admin_analytics()
    print("\n" + "="*60)
    print("📊 ADMIN ANALYTICS RESULTS")
    print("="*60)
    
    print(f"\n📈 OVERVIEW:")
    print(f"   Total Unique Participants: {result['total_unique']}")
    print(f"   Total Responses: {result['total_responses']}")
    print(f"   Avg Events/Participant: {result['engagement']['avg_events_per_participant']}")
    
    print(f"\n🎯 EVENT-WISE:")
    for event in result['events']:
        print(f"   - {event['name']}: {event['count']} responses ({event.get('unique_participants', 'N/A')} unique)")
    
    print(f"\n👥 PARTICIPATION BREAKDOWN:")
    pb = result['participation_breakdown']
    print(f"   Single Event: {pb['single_event']} ({pb['single_event_pct']}%)")
    print(f"   Two Events: {pb['two_events']}")
    print(f"   Three Events: {pb['three_events']}")
    print(f"   Multi-Event Total: {pb['multi_event_total']} ({pb['multi_event_pct']}%)")
    
    print(f"\n🔥 POPULAR EVENT COMBINATIONS:")
    for combo in result['popular_combos'][:5]:
        print(f"   - {combo['combo']}: {combo['count']} participants")
    
    print(f"\n🌟 TOP MULTI-EVENT PARTICIPANTS:")
    for p in result['multi_event_participants'][:5]:
        print(f"   - {p['roll_no']} ({p['dept']}): {p['event_count']} events - {', '.join(p['events'])}")
    
    print(f"\n🏛️ DEPARTMENTS ({result['dept_count']} total):")
    for dept in result['departments'][:5]:
        print(f"   - {dept['name']}: {dept['count']} ({dept['percentage']}%)")
