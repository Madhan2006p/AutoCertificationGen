# Individual Team Member Certificate Control

## 🎯 Feature Overview

This implementation allows **individual certificate control for each team member**, giving admins granular control over who can generate certificates. Each team member now has their own row in the admin dashboard with an independent toggle switch.

## ✨ Key Features

- **Individual Rows**: Each team member gets their own row in the admin dashboard
- **Independent Toggles**: ON/OFF certificate control for every team member
- **Visual Distinction**: Team members are visually differentiated from leaders with:
  - Indented names with 👤 icon
  - Darker background color
  - Blue text color
  - Arrow indicator (↳) in roll number column
- **Leader Summary**: Leaders show a count of team members (e.g., "3 member(s)")
- **Backward Compatible**: Works with existing data and sync processes

## 📊 Database Schema

### New Columns Added:
```python
member_role           TEXT     # 'leader' or 'member'
leader_roll_no        TEXT     # For members, points to leader's roll number
member_position       INTEGER  # Position index of team member (1, 2, 3, ...)
```

### How Records Are Stored:

**Example Team:**
- Leader: John Doe (Roll: 2511001)
- Team Members: Alice Smith, Bob Jones, Charlie Brown

**Database Records:**
```
| ID | roll_no | name       | member_role | leader_roll_no | member_position | blocked |
|----|---------|------------|-------------|----------------|-----------------|---------|
| 1  | 2511001 | John Doe   | leader      | NULL           | 0               | 0       |
| 2  | 2511001 | Alice Smith| member      | 2511001        | 1               | 0       |
| 3  | 2511001 | Bob Jones  | member      | 2511001        | 2               | 0       |
| 4  | 2511001 | Charlie... | member      | 2511001        | 3               | 0       |
```

## 🔄 How It Works

### Data Flow:

1. **Google Sheets Sync** (`backend/sync.py`)
   - Extracts leader information (name, roll, dept, year)
   - Finds all team member name columns
   - Passes leader info + team members list to `save_participant()`

2. **Database Save** (`backend/database.py`)
   - Creates/updates leader record with `member_role='leader'`
   - Deletes old team member records (if any)
   - Creates individual records for each team member
   - Each member gets:
     - Leader's roll number
     - Their own name
     - `member_role='member'`
     - Reference to leader via `leader_roll_no`
     - Position index

3. **Admin Dashboard** (`templates/admin_dashboard.html`)
   - Displays all records in order
   - Leaders shown with full information
   - Team members shown with:
     - Indented layout
     - Visual indicators (icon, arrow)
     - Darker background
     - Individual toggle switch

## 🎨 Visual Design

### Leader Row:
- **Background**: Normal (inherits from parent)
- **Name**: Bold white text
- **Roll Number**: Purple monospace font
- **All Fields**: Fully populated
- **Team Members Column**: Shows count "X member(s)"

### Team Member Row:
- **Background**: Slightly darker (`bg-slate-800/30`)
- **Name**: Blue text with 👤 icon, indented (padding-left)
- **Roll Number**: Gray with ↳ arrow indicator
- **Department/Year**: Shows "-" (not applicable)
- **Each Has**: Own individual toggle switch

### Toggle Switch:
- **ON** (Green): Certificate generation allowed
- **OFF** (Gray): Certificate generation blocked
- **Independent**: Each row has its own toggle

## 📝 Code Examples

### Saving a Team:
```python
from backend.database import save_participant

save_participant(
    roll_no="2511001",
    name="John Doe",
    dept="CSE",
    year="II",
    event="MARKUS 2K26 - Project",
    sheet_source="Project Responses",
    team_members=["Alice Smith", "Bob Jones", "Charlie Brown"]
)
# Creates 4 records: 1 leader + 3 members
```

### Saving an Individual:
```python
save_participant(
    roll_no="2511002",
    name="Jane Doe",
    dept="IT",
    year="II",
    event="MARKUS 2K26 - Project",
    sheet_source="Project Responses"
    # No team_members = only leader record created
)
```

### Toggle Certificate for a Specific Member:
The admin simply clicks the toggle switch for any row (leader or member).

## 🚀 Usage Instructions

### 1. Initialize Database
```bash
python db_init.py
```
This will add the new columns to your existing database.

### 2. Sync Data
Click "🔄 Sync Data" in admin dashboard OR:
```bash
python backend/sync.py
```

This will:
- Read team members from Google Sheets
- Create individual records for each member
- Preserve existing certificate generated status

### 3. Control Certificates
1. Login to admin dashboard (`/admin/login`)
2. Navigate to the participants table
3. For each event, you'll see:
   - Leader row (bold name)
   - Team member rows (indented, with 👤 icon)
4. Toggle the "Show Cert" switch for any individual:
   - **ON**: They can generate certificate
   - **OFF**: Certificate generation blocked for them

## 🔍 Admin Dashboard View

The image above shows exactly how your admin dashboard will look:

1. **John Doe (Leader)** - Full row with all info + toggle
2. **↳ Alice Smith** - Team member, indented, blue text, own toggle
3. **↳ Bob Jones** - Team member, own toggle
4. **↳ Charlie Brown** - Team member, own toggle
5. **Jane Doe** - Individual participant, no team

## ⚙️ Migration

### Automatic Migration:
When you run `db_init.py`, it automatically:
- Adds new columns to existing database
- Sets default values:
  - `member_role = 'leader'` for all existing records
  - `member_position = 0` for leaders
  - `leader_roll_no = NULL` for leaders

### After First Sync:
- Existing leader records remain as-is
- New member records are created for teams
- Old team_members string is preserved in leader record
- Each member gets their own toggle control

## 🧪 Testing

Run the test script:
```bash
python test_individual_members.py
```

Expected output:
```
Adding test team with leader and 3 members...
Adding individual participant...

==========================================================
ID    Roll No      Name                      Role       Leader Roll  Blocked
==========================================================
1     2511001      John Doe (Leader)         leader     -            0
2     2511001      Alice Smith               member     2511001      0
3     2511001      Bob Jones                 member     2511001      0
4     2511001      Charlie Brown             member     2511001      0
5     2511002      Jane Doe                  leader     -            0
==========================================================

✅ Test completed successfully!

Summary:
- Leader record: 1 (John Doe)
- Team member records: 3 (Alice, Bob, Charlie)
- Individual participant: 1 (Jane Doe)
- Total records for this event: 5

Each team member now has their own toggle switch for certificate control!
```

## 📋 Use Cases

### Use Case 1: Block a Specific Team Member
**Scenario**: One team member didn't participate actively.

**Action**:
1. Find the team member's row (e.g., "↳ Bob Jones")
2. Toggle their "Show Cert" switch to OFF
3. Bob cannot generate certificate, but others can

### Use Case 2: Block Entire Team
**Scenario**: Team violated rules.

**Action**:
1. Toggle OFF the leader's switch
2. Toggle OFF each team member's switch
3. Nobody in the team can generate certificates

### Use Case 3: Re-enable After Review
**Scenario**: Issue resolved, allow certificate generation.

**Action**:
1. Toggle ON the specific person's switch
2. They can now generate their certificate

## 🔐 Security & Data Integrity

- Each team member has unique database ID
- Toggles are independent - changing one doesn't affect others
- Leader's toggle doesn't cascade to members (granular control)
- Database constraints ensure data consistency
- Migration is safe and backward compatible

## 📊 Performance

- Minimal overhead: 1 leader + N members = N+1 records
- Indexed by roll_no and event for fast queries
- No complex joins needed for display
- Efficient toggle updates (single record update)

## 🎨 Customization

### Change Team Member Indicator:
In `admin_dashboard.html`, change:
```html
👤 {{ p.name or '-' }}
```
to any icon/text you prefer.

### Change Background Color:
Modify the CSS class:
```html
{% if p.member_role == 'member' %}bg-slate-800/30{% endif %}
```

## ✅ Benefits

1. **Granular Control**: Admin can allow/block any individual
2. **Clear Hierarchy**: Visual distinction between leaders and members
3. **Easy Management**: Each person has their own toggle
4. **Flexibility**: Mixed teams and individuals in same event
5. **Scalability**: Handles any number of team members
6. **Audit Trail**: Each record independently tracked

## 🚧 Important Notes

- Team members use leader's roll number (no separate roll numbers needed)
- Department and Year columns show "-" for members (inherited from leader conceptually)
- Certificate URLs can be generated for each member individually
- Sync process is idempotent - running multiple times is safe

## 🆘 Troubleshooting

**Q: Team members not appearing?**
- Ensure Google Sheet has "Team Member X Name" columns
- Run sync again
- Check sync log for column detection messages

**Q: Toggle not working for a member?**
- Check browser console for errors
- Ensure participant ID is correct
- Verify database record exists

**Q: Old data showing wrong format?**
- Run `python db_init.py` to apply migrations
- Run sync to recreate member records

---

**Last Updated**: 2026-01-26  
**Version**: 2.0 - Individual Team Member Control
