"""
Local Certificate Generation Test Script
Run: python test_cert.py <roll_no>
Example: python test_cert.py 23BCA001
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import get_events_for_roll, init_db
from backend.certificate import generate_local_certificate
from backend.sync import sync_data

def test_generate(roll_no):
    roll_no = roll_no.strip().upper()
    print(f"\n🔍 Searching for roll number: {roll_no}")
    
    # Get events from local DB
    events = get_events_for_roll(roll_no)
    
    if not events:
        print(f"❌ No records found for {roll_no}")
        print("   Try running sync first: python -m backend.sync")
        return
    
    print(f"✅ Found {len(events)} event(s):\n")
    
    for i, event in enumerate(events, 1):
        print(f"--- Event {i} ---")
        print(f"   Event: {event['event']}")
        print(f"   Name: {event['name']}")
        print(f"   Year: {event['year']}")
        print(f"   Department: {event['department']}")
        
        # Generate certificate
        clean_event = event['event'].replace("(Responses)", "").replace("MARKUS 2K26 - ", "").replace("MARKUS ", "").strip()
        
        try:
            filepath = generate_local_certificate(
                name=event['name'] or "TEST NAME",
                year=event['year'] or "I",
                event=clean_event,
                roll_no=roll_no,
                department=event['department'] or ""
            )
            print(f"   ✅ Certificate saved: {filepath}")
        except Exception as e:
            print(f"   ❌ Error generating certificate: {e}")
        print()

if __name__ == "__main__":
    # Initialize DB
    init_db()
    
    if len(sys.argv) < 2:
        print("Usage: python test_cert.py <roll_no>")
        print("Example: python test_cert.py 23BCA001")
        print("\nTo sync data first: python -m backend.sync")
        sys.exit(1)
    
    roll_no = sys.argv[1]
    test_generate(roll_no)
