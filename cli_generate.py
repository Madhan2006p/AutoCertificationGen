import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.certificate import generate_local_certificate

def main():
    print("=== Certificate Generator CLI ===")
    try:
        name = input("Enter Name: ").strip()
        if not name:
            print("Name cannot be empty.")
            return

        roll_no = input("Enter Roll No: ").strip()
        if not roll_no:
            print("Roll No cannot be empty.")
            return

        year = input("Enter Year (1/2/3/4): ").strip()
        if not year:
            print("Year cannot be empty.")
            return
            
        department = input("Enter Department (Optional, press Enter to skip): ").strip()

        event = input("Enter Event: ").strip()
        if not event:
            print("Event cannot be empty.")
            return

        print("\nGenerating certificate...")
        
        filepath = generate_local_certificate(
            name=name,
            year=year,
            event=event,
            roll_no=roll_no,
            department=department
        )
        
        print(f"✅ Certificate successfully generated!")
        print(f"📂 Location: {filepath}")

    except KeyboardInterrupt:
        print("\nOperation cancelled.")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
