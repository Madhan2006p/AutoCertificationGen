# Team Members Feature Implementation

## Overview
This implementation adds the ability to display team member names for each event in the Admin dashboard. The feature automatically detects and extracts team member names from Google Sheets columns.

## Changes Made

### 1. Database Schema Update (`backend/database.py`)
- Added `team_members` column to the `participants` table
- Stores team member names as a comma-separated string
- Added migration logic to update existing databases automatically
- Updated `save_participant()` function to accept optional `team_members` parameter

**Key Changes:**
```python
# New column in CREATE TABLE
team_members TEXT

# Migration for existing databases
cursor.execute("ALTER TABLE participants ADD COLUMN team_members TEXT")

# Updated function signature
def save_participant(roll_no, name, dept, year, event, sheet_source, team_members=None):
```

### 2. Data Sync Logic Update (`backend/sync.py`)
- Enhanced to automatically detect team member name columns in Google Sheets
- Searches for columns containing "team member" or "member" + "name" keywords
- Extracts all team member names and stores them as comma-separated values
- Backward compatible - works with sheets that don't have team member columns

**Key Logic:**
```python
# Find all team member name columns
team_member_indices = []
for idx, h in enumerate(headers):
    h_lower = h.lower()
    if ("team member" in h_lower or "member" in h_lower) and "name" in h_lower:
        team_member_indices.append(idx)

# Extract and join team member names
team_members_list = []
for tm_idx in team_member_indices:
    if tm_idx < len(row) and row[tm_idx].strip():
        team_members_list.append(row[tm_idx].strip())

team_members = ", ".join(team_members_list) if team_members_list else None
```

### 3. Admin Dashboard UI Update (`templates/admin_dashboard.html`)
- Added "Team Members" column to the participant table
- Displays team member names in blue color for easy visibility
- Shows "-" when no team members are present
- Responsive and fits within the existing design

**UI Changes:**
- New table header: "Team Members"
- New table cell with conditional display:
  - If team members exist: Display in blue color
  - If no team members: Display "-" in gray

## How It Works

### Data Flow:
1. **Google Sheets** → Contains columns like "Team Member 1 Name", "Team Member 2 Name", etc.
2. **Sync Process** (`sync.py`) → Automatically detects and extracts team member names
3. **Database** (`database.py`) → Stores team members as comma-separated string
4. **Admin Dashboard** (`admin_dashboard.html`) → Displays team members for each participant

### Column Detection:
The sync process looks for columns that match these patterns:
- Contains "team member" AND "name"
- Contains "member" AND "name"

Examples of detected columns:
- "Team Member 1 Name"
- "Team Member 2 Name"
- "Member Name"
- "Team members names"

## Usage

### 1. Initialize/Update Database
```bash
python db_init.py
```

### 2. Sync Data from Google Sheets
- Option A: Via Admin Dashboard - Click "🔄 Sync Data" button
- Option B: Via Command Line:
```bash
python backend/sync.py
```

### 3. View Team Members
1. Login to Admin Dashboard at `/admin/login`
2. Navigate to the dashboard
3. View the "Team Members" column for each event
4. Team member names will appear as comma-separated values

## Testing

A test script is provided: `test_team_members.py`

```bash
python test_team_members.py
```

This will:
- Initialize the database
- Add test participants with and without team members
- Verify the data is stored and retrieved correctly

## Backward Compatibility

✅ **Fully backward compatible:**
- Existing code works without modification
- `save_participant()` has optional `team_members` parameter
- Sheets without team member columns work as before
- Database migration handles both new and existing databases

## Google Sheets Format

### Recommended Column Names:
- "Team Member 1 Name"
- "Team Member 2 Name"
- "Team Member 3 Name"
- etc.

### Example Sheet Structure:
| Roll No | Name | Department | Year | Team Member 1 Name | Team Member 2 Name | Team Member 3 Name |
|---------|------|------------|------|-------------------|-------------------|-------------------|
| 2511001 | John Doe | CSE | II | Alice Smith | Bob Jones | Charlie Brown |
| 2511002 | Jane Doe | IT | II | - | - | - |

## UI Preview

In the Admin Dashboard, you'll see:

```
Roll No    Name        Department  Year  Team Members                           Certificate  Show Cert
2511001    John Doe    CSE         II    Alice Smith, Bob Jones, Charlie Brown  📄 View      ✓
2511002    Jane Doe    IT          II    -                                      Not generated ✓
```

## Notes

- Team members are displayed in **blue color** for easy visibility
- Empty or missing team member columns show as "-"
- The feature automatically handles varying numbers of team members
- No manual configuration needed - column detection is automatic
