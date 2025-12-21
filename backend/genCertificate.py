from PIL import Image, ImageDraw, ImageFont
import os

BASE_DIR = os.path.dirname(__file__)
FONT_DIR = os.path.join(BASE_DIR, "fonts")

def generate_certificate(name, roll_no, event):
    """
    Generate certificate with precise text positioning
    
    Args:
        name: Student name
        roll_no: Roll number/Registration number
        event: Event name (e.g., "Paper Presentation", "Project Demo")
    """
    # Load template
    img = Image.open("backend/Quantumfest.png")
    draw = ImageDraw.Draw(img)
    
    # Get image dimensions for reference
    img_width, img_height = img.size
    print(f"Template size: {img_width}x{img_height}")
    # Load fonts with appropriate sizes
    # Name font - bold, medium size
    font_name = ImageFont.truetype(
       os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf"), 50
    )
    # Roll number font - regular, smaller
    font_roll = ImageFont.truetype(
        os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf"), 45
    )
    # Event name font - bold, larger
    font_event = ImageFont.truetype(
        os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf"), 45
    )

    # Text preparation
    name_text = name.upper()
    roll_text = roll_no
    event_text = event.upper()

    # POSITION COORDINATES (based on certificate layout)
    # These positions are calculated from the template analysis
    
    # Name position - after "This is to certify that Mr./Ms. "
    NAME_X = 1140
    NAME_Y = 666
    
    # Roll number position - on the second blank line after "of ____"
    ROLL_X = 218
    ROLL_Y = 783
    
    # Event name position - on the second blank line after "has participated in ____"
    EVENT_X = 1044
    EVENT_Y = 769

    # Draw name (black color)
    draw.text(
        (NAME_X, NAME_Y),
        name_text,
        fill="black",
        font=font_name,
        anchor="lt"  # left-top anchor
    )

    # Draw roll number (black color)
    draw.text(
        (ROLL_X, ROLL_Y),
        roll_text,
        fill="black",
        font=font_roll,
        anchor="lt"
    )

    # Draw event name (dark blue color to match "QUANTUM FEST 2k25")
    draw.text(
        (EVENT_X, EVENT_Y),
        event_text,
        fill="#1a2c5b",  # Dark blue color
        font=font_event,
        anchor="lt"
    )

    # Create output directory if it doesn't exist
    os.makedirs("backend/certificates", exist_ok=True)
    
    # Save certificate (PNG format - quality/dpi not needed for PNG)
    filename = f"backend/certificates/{roll_no}_{event.replace(' ', '_')}.png"
    img.save(filename)
    
    print(f"✓ Certificate generated: {filename}")
    return filename

