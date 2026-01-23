from PIL import Image, ImageDraw, ImageFont
import os

# Coordinates from request
# Name: (767, 1184) Left-Middle
# Year: (533, 294) Left-Middle
# Event: (1301, 294) Left-Middle

COORD_NAME = (767, 1184)
COORD_YEAR = (533, 294)
COORD_EVENT = (1301, 294)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(BASE_DIR, "Participation.png")
# We assume a fonts folder exists, or we use default
FONT_PATH = os.path.join(BASE_DIR, "fonts", "DejaVuSans-Bold.ttf")

def generate_local_certificate(name, year, event, roll_no):
    if not os.path.exists(TEMPLATE_PATH):
        raise FileNotFoundError(f"Template not found: {TEMPLATE_PATH}")

    img = Image.open(TEMPLATE_PATH)
    draw = ImageDraw.Draw(img)

    # Load Fonts
    try:
        font_large = ImageFont.truetype(FONT_PATH, 45) # For Name
        font_small = ImageFont.truetype(FONT_PATH, 35) # For Year/Event
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Draw Text
    # Anchor 'lm' = Left Middle
    draw.text(COORD_NAME, str(name).upper(), fill="black", font=font_large, anchor="lm")
    draw.text(COORD_YEAR, f"{year} YEAR", fill="black", font=font_small, anchor="lm")
    draw.text(COORD_EVENT, str(event).upper(), fill="black", font=font_small, anchor="lm")

    # Output
    out_dir = os.path.join(BASE_DIR, "generated")
    os.makedirs(out_dir, exist_ok=True)
    
    filename = f"{roll_no}_{event.replace(' ', '_')}.png"
    filepath = os.path.join(out_dir, filename)
    
    img.save(filepath)
    return filepath
