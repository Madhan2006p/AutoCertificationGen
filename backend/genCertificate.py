from PIL import Image, ImageDraw, ImageFont
import os

BASE_DIR = os.path.dirname(__file__)
FONT_DIR = os.path.join(BASE_DIR, "fonts")

def generate_certificate(name, roll_no, event, year):
    """
    Generate certificate with precise text positioning using Participation.png
    """
    # Load template
    template_path = os.path.join(BASE_DIR, "Participation.png")
    
    if not os.path.exists(template_path):
        print(f"Error: Template not found at {template_path}")
        # Fallback for local testing if needed, but best to fail loudly
        return None

    img = Image.open(template_path)
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    try:
        font_name = ImageFont.truetype(os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf"), 45)
        font_other = ImageFont.truetype(os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf"), 35)
    except Exception as e:
        print(f"Error loading fonts: {e}")
        # Fallback to default if custom font fails (though less likely)
        font_name = ImageFont.load_default()
        font_other = ImageFont.load_default()

    # Text preparation
    name_text = name.upper()
    year_text = f"{year} YEAR" if year else ""
    event_text = event.upper()
    dept_text = "" # Dept is not passed in args here? Wait, arguments are (name, roll_no, event, year).
    # The previous caller didn't pass dept. To fix this fully, we might need to fetch dept or change signature.
    # However, Looking at generate_participation.py, it takes (record, roll_col, event_name, dept_col) and extracts.
    # The caller in app.py calls: generate_and_upload_cert(roll_no, name, event, year)
    # And tasks.py calls: generate_certificate(name, roll_no, event, year)
    # WE ARE MISSING DEPARTMENT IN THE ARGUMENTS.
    # For now, let's just make it work with what we have. If Dept is required, we need to ask user or fetch it.
    # BUT wait, the user request "Department : x : 854 , y : 294 + Year : x : 533 , y : 294" implies Dept is needed.
    # Let me check where `genCertificate.py` is called. It's called by `tasks.py`.
    # And `tasks.py` is called by `app.py`.
    # `app.py` has `user_record` from `ap.get_user_by_reg(roll)`.
    # `ap.get_user_by_reg` returns dataframe from sqlite `participants`.
    # `db_refresh.py` does NOT save department to sqlite `participants`. It only saves roll_no, name, year, event.
    # STOP. I need to fix `db_refresh.py` to save Department first if I want to put it on cert.
    # OR, I just leave it blank for now? No, User explicitely asked for Department.
    
    # Let's fix `genCertificate` first to use new coords.
    
    # Coordinates from generate_participation.py
    # Name : 767, 1184 (Left Anchor)
    # Year : 533, 294 (Left Anchor)
    # Event : 1301, 294 (Left Anchor)
    # Dept : 854, 294 (Left Anchor) - We don't have Dept yet.
    
    draw.text((767, 1184), name_text, fill="black", font=font_name, anchor="lm")
    draw.text((533, 294), year_text, fill="black", font=font_other, anchor="lm")
    draw.text((1301, 294), event_text, fill="black", font=font_other, anchor="lm")
    
    # Placeholder for Dept until we fix DB
    # draw.text((854, 294), "DEPT", fill="black", font=font_other, anchor="lm") 

    # Create output directory
    output_dir = os.path.join(BASE_DIR, "certificates")
    os.makedirs(output_dir, exist_ok=True)
    
    filename = os.path.join(output_dir, f"{roll_no}_{event.replace(' ', '_')}.png")
    img.save(filename)
    
    print(f"✓ Certificate generated: {filename}")
    return filename

