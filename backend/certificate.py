from PIL import Image, ImageDraw, ImageFont
import os

# Coordinates from request
# Name: (767, 1184) Left-Middle
# Year: (533, 294) Left-Middle
# Event: (1301, 294) Left-Middle

COORD_NAME = (1064, 786)
COORD_YEAR = (315,865 )
COORD_EVENT = (1264, 865)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(BASE_DIR, "Participation.png")
# We assume a fonts folder exists, or we use default
FONT_PATH = os.path.join(BASE_DIR, "fonts", "DejaVuSans-Bold.ttf")

def generate_local_certificate(name, year, event, roll_no, department=""):
    if not os.path.exists(TEMPLATE_PATH):
        raise FileNotFoundError(f"Template not found: {TEMPLATE_PATH}")

    img = Image.open(TEMPLATE_PATH)
    draw = ImageDraw.Draw(img)

    # Load Fonts - try multiple options
    font_large = None
    font_small = None
    
    # List of fonts to try (in order of preference)
    font_paths = [
        os.path.join(BASE_DIR, "fonts", "DejaVuSans-Bold.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux/Render
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/arial.ttf",  # Windows fallback
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font_large = ImageFont.truetype(fp, 45)
                font_small = ImageFont.truetype(fp, 35)
                print(f"Using font: {fp}")
                break
            except Exception as e:
                print(f"Failed to load {fp}: {e}")
                continue
    
    if not font_large:
        print("WARNING: No custom font found, using default (may be tiny)")
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Convert Year to Roman if numeric
    roman_map = {"1": "I", "2": "II", "3": "III", "4": "IV"}
    clean_year = str(year).strip()
    year_roman = roman_map.get(clean_year, clean_year)

    # Format: "Department Year" (e.g., "CSE III Year")
    dept_year_text = f"{department} {year_roman} Year" if department else f"{year_roman} Year"

    # Draw Text
    # Anchor 'lm' = Left Middle
    draw.text(COORD_NAME, str(name).upper(), fill="black", font=font_large, anchor="lm")
    draw.text(COORD_YEAR, dept_year_text.upper(), fill="black", font=font_small, anchor="lm")
    draw.text(COORD_EVENT, str(event).upper(), fill="black", font=font_small, anchor="lm")

    # Add Footer Text
    footer_text = "CT-PG Association Club | CT-PG Coding Club"
    # Centered at bottom
    W, H = img.size
    # Using smaller font for footer
    font_footer = font_small
    try:
        # Check if we can load a slightly smaller/different font? reusing font_small for now (size 35)
        # Maybe scale it down to 25?
        if font_large.path: # If we have a path from before
             font_footer = ImageFont.truetype(font_large.path, 25)
    except:
        pass
        
    draw.text((W/2, H - 50), footer_text, fill="black", font=font_footer, anchor="mm")

    # Output
    out_dir = os.path.join(BASE_DIR, "generated")
    os.makedirs(out_dir, exist_ok=True)
    
    filename = f"{roll_no}_{event.replace(' ', '_')}.png"
    filepath = os.path.join(out_dir, filename)
    
    img.save(filepath)
    return filepath
