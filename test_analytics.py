from backend.admin_analytics import fetch_admin_analytics

# Fetch and display analytics
analytics = fetch_admin_analytics()

print("\n" + "="*60)
print("EVENT SUMMARY")
print("="*60)

for event in analytics["events"]:
    print(f"{event['name']:20s} - {event['count']:3d} responses, {event['unique_participants']:3d} unique participants")

print(f"\nTotal Unique Participants: {analytics['total_unique']}")
print(f"Total Responses: {analytics['total_responses']}")
