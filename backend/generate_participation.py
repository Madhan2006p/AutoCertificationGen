
import gspread
import os
import sys
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# Ensure we can import from the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Load sheet configurations from admin_analytics to match Admin Login/Dashboard links
    from admin_analytics import get_gspread_client, SHEET_CONFIGS, normalize_department
except ImportError:
    # If running from root
    sys.path.append(os.path.join(os.getcwd(), 'backend'))
    from admin_analytics import get_gspread_client, SHEET_CONFIGS, normalize_department

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, "fonts", "DejaVuSans-Bold.ttf")
TEMPLATE_PATH = os.path.join(BASE_DIR, "Participation.png")
OUTPUT_DIR = os.path.join(BASE_DIR, "certificates")

def get_year_from_roll(roll_no):
    """
    Calculate year based on roll number prefix.
    Assumes roll number starts with 2 digits representing year (e.g. 23XXX).
    Current Academic Year Context: 2025-2026 (MarkUs 2K26)
    25 Batch -> I Year
    24 Batch -> II Year
    23 Batch -> III Year
    22 Batch -> IV Year
    """
    if not roll_no or len(roll_no) < 2:
        return ""
    
    try:
        # Extract first specific digits. Try strict 2 digits.
        prefix = roll_no[:2]
        if prefix.isdigit():
            val = int(prefix)
            # Map batch to year
            if val == 25: return "I"
            if val == 24: return "II"
            if val == 23: return "III"
            if val == 22: return "IV"
            if val == 21: return "IV+" # or Alumni
    except:
        pass
    
    return ""

def find_best_name_column(record, roll_col_name):
    """
    Find the corresponding name column for a given roll number column.
    """
    headers = list(record.keys())
    
    # 1. Try replacing "Roll no" with "Name" keywords in the column name
    keywords_to_replace = ["Roll no", "Roll number", "Roll No", "Roll Number", "ROLL NO"]
    
    roll_lower = roll_col_name.lower()
    
    # Heuristic 1: If it's a team member/leader specific column
    if "leader" in roll_lower:
        for h in headers:
            h_lower = h.lower()
            if "leader" in h_lower and ("name" in h_lower) and h != roll_col_name:
                return h
    
    if "member 1" in roll_lower:
        for h in headers:
            h_lower = h.lower()
            if "member 1" in h_lower and ("name" in h_lower) and h != roll_col_name:
                return h
                
    if "member 2" in roll_lower:
        for h in headers:
            h_lower = h.lower()
            if "member 2" in h_lower and ("name" in h_lower) and h != roll_col_name:
                return h
                
    # Heuristic 2: Look for generic "Name" if it's the only roll column or primary
    # Common headers: "Name with initial", "Name", "Student Name"
    priority_names = ["Name with initial (eg:Anu A)", "Name", "Student Name", "Full Name"]
    for p in priority_names:
        if p in headers:
            return p
            
    # Heuristic 3: Search for any column containing "name"
    for h in headers:
        if "name" in h.lower() and "team" not in h.lower() and "file" not in h.lower():
             return h

    return None

def generate_certificate(record, roll_col, event_name, dept_col):
    """
    Generate a certificate for a single entry.
    """
    roll_no = record.get(roll_col, "").strip().upper()
    if not roll_no or len(roll_no) < 5:
        return
        
    name_col = find_best_name_column(record, roll_col)
    if not name_col:
        print(f"Skipping {roll_no}: Could not find name column for {roll_col}")
        return
        
    name = record.get(name_col, "").strip().upper()
    # "Who are the name in form only get genrated"
    if not name:
        return

    dept = normalize_department(record.get(dept_col, ""))
    year_val = get_year_from_roll(roll_no)
    
    # Create image
    try:
        img = Image.open(TEMPLATE_PATH)
        draw = ImageDraw.Draw(img)
        
        # Load Font
        try:
            # Adjust sizes as needed. User didn't specify size, I'll estimate.
            font_size_name = 45 
            font_size_other = 35
            font_name = ImageFont.truetype(FONT_PATH, font_size_name)
            font_other = ImageFont.truetype(FONT_PATH, font_size_other)
        except Exception as e:
            print(f"Error loading font: {e}")
            return

        # Coordinates
        # Name : x : 767 , y : 1184 
        # Department : x : 854 , y : 294 
        # Year : x : 533 , y : 294 
        # Event : x : 1301 , y : 294
        
        # Draw Name
        draw.text((767, 1184), name, fill="black", font=font_name, anchor="ms") # Middle-Bottom anchoring or similar?
        # User gave one point. Usually assumes left-aligned or centered?
        # If specific x,y given, usually it's the starting point (left-top or left-baseline).
        # "Name : x : 767" -> If it's centered text, anchor="mm" or "mt". 
        # Let's assume Left aligned for now unless it looks like a center point.
        # 767 is roughly middle of a 1080p width? No, 1920 width. 767 is left-ish.
        # Wait, standard A4 is 2480 px width at 300dpi. 
        # Previous cert code used 1140 for Name (Center?).
        # 767 seems specific. I'll use anchor="lm" (Left Middle) or "ls" (Left Baseline).
        # Let's use "xy" generic (Left Top usually).
        
        draw.text((767, 1184), name, fill="black", font=font_name, anchor="lm")
        
        # Dept
        draw.text((854, 294), dept, fill="black", font=font_other, anchor="lm")
        
        # Year
        year_text = f"{year_val} YEAR" if year_val else ""
        draw.text((533, 294), year_text, fill="black", font=font_other, anchor="lm")
        
        # Event
        draw.text((1301, 294), event_name.upper(), fill="black", font=font_other, anchor="lm")
        
        # Save
        event_s = event_name.replace(" ", "_")
        roll_s = roll_no.replace("/", "_")
        filename = f"{OUTPUT_DIR}/{event_s}_{roll_s}.png"
        img.save(filename)
        print(f"Generated: {filename}")
        
    except Exception as e:
        print(f"Error generating for {roll_no}: {e}")

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    client = get_gspread_client()
    if not client:
        return

    for config in SHEET_CONFIGS:
        print(f"Processing {config['display_name']}...")
        try:
            sheet = client.open(config["name"]).sheet1
            all_records = sheet.get_all_records()
            
            # Handle empty headers issue in get_all_records?
            # get_all_records might fail if duplicate keys.
            # safe approach: get_all_values and map manually (like in admin_analytics)
            # But let's try get_all_records first, if it fails, fallback.
            
            # Actually admin_analytics uses manual mapping. I should copy that to be safe.
        except Exception as e:
            print(f"Error opening sheet {config['name']}: {e}")
            continue

        # Use manual extraction logic from admin_analytics to be safe against duplicate headers
        try:
            worksheet = sheet
            headers = worksheet.row_values(1)
            all_values = worksheet.get_all_values()
            
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
            
            # Now iterate records
            for record in records:
                for roll_col in config["roll_columns"]:
                    generate_certificate(
                        record, 
                        roll_col, 
                        config["display_name"], 
                        config["dept_column"]
                    )
                    
        except Exception as e:
            print(f"Error processing records for {config['name']}: {e}")

if __name__ == "__main__":
    main()
