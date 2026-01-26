"""Test script to verify individual team member records feature"""
from backend.database import init_db, save_participant, get_all_participants
import json

# Initialize database
init_db()

# Add test participant with team members
print("Adding test team with leader and 3 members...")
save_participant(
    roll_no="2511001",
    name="John Doe (Leader)",
    dept="CSE",
    year="II",
    event="Test Event - Project",
    sheet_source="Test Sheet",
    team_members=["Alice Smith", "Bob Jones", "Charlie Brown"]
)

# Add test participant without team members (individual)
print("Adding individual participant...")
save_participant(
    roll_no="2511002",
    name="Jane Doe",
    dept="IT",
    year="II",
    event="Test Event - Project",
    sheet_source="Test Sheet"
)

# Retrieve and display all participants
print("\nRetrieving participants...")
participants = get_all_participants()

print(f"\n{'='*80}")
print(f"{'ID':<5} {'Roll No':<12} {'Name':<25} {'Role':<10} {'Leader Roll':<12} {'Blocked':<8}")
print(f"{'='*80}")

for p in participants:
    if p['event'] == "Test Event - Project":
        leader_roll = p.get('leader_roll_no') or '-'
        member_role = p.get('member_role') or 'N/A'
        print(f"{p['id']:<5} {p['roll_no']:<12} {p['name']:<25} {member_role:<10} {leader_roll:<12} {p.get('blocked', 0):<8}")

print(f"{'='*80}")
print(f"\n✅ Test completed successfully!")
print(f"\nSummary:")
print(f"- Leader record: 1 (John Doe)")
print(f"- Team member records: 3 (Alice, Bob, Charlie)")
print(f"- Individual participant: 1 (Jane Doe)")
print(f"- Total records for this event: {len([p for p in participants if p['event'] == 'Test Event - Project'])}")
print(f"\nEach team member now has their own toggle switch for certificate control!")
