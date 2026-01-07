import os
import sqlite3
import cloudinary
import cloudinary.uploader
from backend.genCertificate import generate_certificate

# Cloudinary Configuration
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

def generate_and_upload_cert(roll_no, name, event, year):
    """
    Generate certificate, upload to Cloudinary, and update database.
    This is called exclusively by app.py after race condition checks.
    """
    print(f"Generating certificate for {roll_no} - {event}...")
    
    # 1. Generate local file
    try:
        path = generate_certificate(name, roll_no, event, year)
    except Exception as e:
        print(f"Error generating certificate: {e}")
        return None

    # 2. Upload to Cloudinary
    print(f"Uploading {path} to Cloudinary...")
    try:
        upload_result = cloudinary.uploader.upload(
            path, 
            resource_type="image", 
            folder="certificates",
            public_id=f"{roll_no}_{event.replace(' ', '_')}"
        )
        cert_url = upload_result.get("secure_url")
        print(f"Upload successful: {cert_url}")
    except Exception as e:
        print(f"Error uploading to Cloudinary: {e}")
        return None

    # 3. Update database
    try:
        conn = sqlite3.connect("forms_data.db")
        cursor = conn.cursor()
        
        # Guard against missing column
        try:
            cursor.execute("ALTER TABLE participants ADD COLUMN cert_url TEXT")
        except sqlite3.OperationalError:
            pass
            
        cursor.execute(
            "UPDATE participants SET cert_url = ? WHERE roll_no = ? AND event = ?",
            (cert_url, roll_no, event)
        )
        conn.commit()
        conn.close()
        print(f"✅ Database updated for {roll_no}")
    except Exception as e:
        print(f"❌ Error updating database: {e}")
        
    return cert_url
