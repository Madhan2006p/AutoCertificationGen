from PIL import Image, ImageDraw, ImageFont
import os

BASE_DIR = os.path.dirname(__file__)
FONT_DIR = os.path.join(BASE_DIR, "fonts")

def generate_certificate(name, roll_no, event, year, dept=""):
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
    dept_text = dept.upper() if dept else ""

    # POSITION COORDINATES (based on certificate layout)
    # These positions are calculated from the template analysis
    
    # Name position - after "This is to certify that Mr./Ms. "
    NAME_X = 1140
    NAME_Y = 666
    
    # Roll number position - on the second blank line after "of ____"
    ROLL_X = 223
    ROLL_Y = 770
    
    # Event name position - on the second blank line after "has participated in ____"
    EVENT_X = 1044
    EVENT_Y = 769

    # Draw name (black color)
    draw.text(
        (767, 1184),
        name_text,
        fill="black",
        font=font_name,
        anchor="lm"  # left-middle anchor
    )

    # Draw Year
    draw.text(
        (533, 294),
        year_text,
        fill="black",
        font=font_other,
        anchor="lm"
    )

    # Draw Department
    draw.text(
        (854, 294),
        dept_text,
        fill="black",
        font=font_other,
        anchor="lm"
    )

    # Draw event name
    draw.text(
        (1301, 294),
        event_text,
        fill="black",  # Updated to black as per request context
        font=font_other,
        anchor="lm"
    )

