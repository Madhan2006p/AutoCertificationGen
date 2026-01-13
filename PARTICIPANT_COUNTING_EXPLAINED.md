# Participant Counting Logic - Team Members Included ✅

## 🎯 How Unique Participation is Calculated

### **Important: ALL team members are counted individually!**

## 📊 Counting Logic

### For Each Event:

1. **Team/Response Count** (`count`):
   - Number of form responses/registrations
   - Example: 10 teams registered

2. **Unique Participants** (`unique_participants`):
   - **ALL individual team members** from all teams
   - Counts: Team Leader + Team Member 1 + Team Member 2 + etc.
   - Example: 10 teams × 3 members = up to 30 participants

### Example Breakdown:

**Code Adapt Event:**
- Configuration: Tracks 3 columns per team:
  - Team Leader Roll no
  - Team member 1 Roll number
  - Team member 2 Roll number
- If 15 teams register:
  - `count` = 15 (teams/responses)
  - `unique_participants` = ~45 (15 teams × 3 members)
  - *Note: May be less than 45 if some teams have fewer members*

**UI/UX Design Event:**
- Configuration: Tracks 1 column (solo event):
  - Roll no
- If 20 people register:
  - `count` = 20 (responses)
  - `unique_participants` = 20 (individuals)

## 🌟 Overall Statistics

**Total Unique Participants:**
- Counts EVERY individual who participated in ANY event
- Removes duplicates (if someone participated in multiple events)
- Example:
  - Alice participated in Code Adapt + UI/UX = counted ONCE
  - Bob participated in Technical Quiz only = counted ONCE
  - Total Unique = All unique roll numbers across all events

**Multi-Event Participation:**
- Tracks individuals who joined 2, 3, 4, or more events
- Based on individual roll numbers, not teams

## 📋 Configuration per Event

```python
SHEET_CONFIGS = [
    {
        "name": "MARKUS 2K26 -  CODE ADAPT (Responses)",
        "roll_columns": [
            "Team Leader Roll no (eg : 23XXX001)",      # Person 1
            "Team member 1 Roll number (eg:23XXX001)",  # Person 2
            "Team member 2 Roll number (eg:23XXX001)"   # Person 3
        ]
        # → Counts 3 people per team
    },
    {
        "name": "UI/UX  (Responses)",
        "roll_columns": [
            "Roll no (eg:23XXX001)"  # Solo participant
        ]
        # → Counts 1 person per response
    }
]
```

## ✅ What This Means

### Admin Dashboard Shows:

**Event Statistics:**
- **Code Adapt:** "15 teams/responses → 42 participants"
  - 15 teams registered
  - 42 individual students participated (some teams may have 2 members instead of 3)

- **UI/UX Design:** "20 teams/responses → 20 participants"
  - 20 individual registrations
  - 20 participants (solo event)

**Overall Statistics:**
- **Total Unique Participants:** 150
  - 150 different students participated across all events
  - Each student counted once, regardless of how many events they joined

- **Multi-Event Participation:**
  - Single Event: 80 students (participated in 1 event only)
  - Two Events: 50 students (participated in 2 events)
  - Three+ Events: 20 students (participated in 3 or more events)

## 🔍 How It Works (Technical)

1. **Extract Roll Numbers:**
   ```python
   # For each response, extract all roll numbers from configured columns
   roll_numbers = extract_roll_numbers_from_row(record, roll_columns)
   # Returns: ["23ISR001", "23ISR002", "23ISR003"]
   ```

2. **Track Participants:**
   ```python
   # Add each roll number to the event's participant set
   for roll_no in roll_numbers:
       event_participants[event_name].add(roll_no)
       roll_to_events[roll_no].add(event_name)  # Track which events each person joined
   ```

3. **Calculate Unique:**
   ```python
   unique_participants = len(event_participants[event_name])
   # Set automatically removes duplicates
   ```

## 📈 Output Format

**Console Output:**
```
📊 Fetching: MARKUS 2K26 -  CODE ADAPT (Responses)...
   ✅ Code Adapt: 15 teams/responses → 42 unique participants

📊 Fetching: UI/UX  (Responses)...
   ✅ UI/UX Design: 20 teams/responses → 20 unique participants
```

**Analytics Result:**
```json
{
  "events": [
    {
      "name": "Code Adapt",
      "count": 15,                    // Teams/responses
      "unique_participants": 42       // All individual team members
    }
  ],
  "total_unique": 150,                // All unique students across all events
  "total_responses": 85               // Total form submissions
}
```

---

## ✅ Summary

**Yes, ALL team members are counted!** The system:
1. ✅ Extracts all roll numbers from each team registration
2. ✅ Counts each individual student separately
3. ✅ Tracks which events each student participated in
4. ✅ Removes duplicates for overall totals
5. ✅ Shows clear distinction between teams and participants

**Updated:** 2026-01-13
**Commit:** `88346a2`
