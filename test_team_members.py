"""Test script to verify team members feature"""
from backend.database import init_db, save_participant, get_all_participants

# Initialize database
init_db()

# Add test participant with team members
print("Adding test participant with team members...")
save_participant(
    roll_no="2511001",
    name="John Doe",
    dept="CSE",
    year="II",
    event="Test Event",
    sheet_source="Test Sheet",
    team_members="Alice Smith, Bob Jones, Charlie Brown"
)

# Add test participant without team members
print("Adding test participant without team members...")
save_participant(
    roll_no="2511002",
    name="Jane Doe",
    dept="IT",
    year="II",
    event="Test Event",
    sheet_source="Test Sheet"
)

# Retrieve and display all participants
print("\nRetrieving participants...")
participants = get_all_participants()
for p in participants:
    print(f"\n{p['name']} ({p['roll_no']})")
    print(f"  Event: {p['event']}")
    print(f"  Team Members: {p.get('team_members', 'None')}")

print("\n✅ Test completed successfully!")
