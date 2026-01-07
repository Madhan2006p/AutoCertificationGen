import sqlite3
import os
from tasks import generate_and_upload_cert
from dotenv import load_dotenv

load_dotenv()

def pre_generate_all():
    """
    Fetch all participants from the database and generate/upload certificates synchronously.
    This architecture avoids the need for a separate Redis worker for 500 users.
    """
    conn = sqlite3.connect("forms_data.db")
    cursor = conn.cursor()
    
    # Ensure cert_url column exists
    try:
        cursor.execute("ALTER TABLE participants ADD COLUMN cert_url TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    # Find records that don't have a certificate yet
    cursor.execute("SELECT roll_no, name, event, year FROM participants WHERE cert_url IS NULL OR cert_url = ''")
    records = cursor.fetchall()
    conn.close()

    if not records:
        print("✅ No pending certificates to generate.")
        return

    print(f"📑 Found {len(records)} records needing certificates. Starting synchronous generation...")

    success_count = 0
    fail_count = 0

    for roll_no, name, event, year in records:
        try:
            print(f"⏳ Processing: {roll_no} - {event}...")
            url = generate_and_upload_cert(roll_no, name, event, year)
            if url:
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            print(f"❌ Error for {roll_no}: {e}")
            fail_count += 1
            
    print(f"\n✨ Generation Complete!")
    print(f"✅ Success: {success_count}")
    print(f"❌ Failed: {fail_count}")

if __name__ == "__main__":
    pre_generate_all()
