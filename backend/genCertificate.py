from PIL import Image, ImageDraw, ImageFont

def generate_certificate(name, roll_no, event):
    img = Image.open("certificate_template.png")
    draw = ImageDraw.Draw(img)

    # Fonts
    font_name = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 70)
    font_event = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 85)
    font_small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 45)

    # Text values
    name_reg = f"{name.upper()} ({roll_no})"
    event_text = event.upper()
    thanks_text = "Thank you for participating"

    # 🔹 EXACT positions from Canva
    NAME_X, NAME_Y = 435, 350
    EVENT_X, EVENT_Y = 435, 523
    # THANKS_X, THANKS_Y = 435, 760   # you can fine-tune this

    # Draw text (start from X,Y)
    draw.text(
        (NAME_X, NAME_Y),
        name_reg,
        fill="black",
        font=font_name,
        anchor="la"
    )

    draw.text(
        (EVENT_X, EVENT_Y),
        event_text,
        fill="#1a2c5b",
        font=font_event,
        anchor="la"
    )


    # Save certificate
    filename = f"certificates/{roll_no}_{event.replace(' ', '_')}.png"
    img.save(filename)

    print("Generated:", filename)
