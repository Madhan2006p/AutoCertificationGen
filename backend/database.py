import sqlite3
import os

DB_PATH = "participants.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Simple flat structure
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT NOT NULL,
            name TEXT,
            department TEXT,
            year TEXT,
            event TEXT NOT NULL,
            sheet_source TEXT,
            cert_url TEXT,
            blocked INTEGER DEFAULT 0,
            team_members TEXT,
            member_role TEXT DEFAULT 'leader',
            leader_roll_no TEXT,
            member_position INTEGER DEFAULT 0
        )
    """)
    
    # Add blocked column if missing (migration for existing DB)
    try:
        cursor.execute("ALTER TABLE participants ADD COLUMN blocked INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Add team_members column if missing (migration for existing DB)
    try:
        cursor.execute("ALTER TABLE participants ADD COLUMN team_members TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Add member_role column if missing (migration for existing DB)
    try:
        cursor.execute("ALTER TABLE participants ADD COLUMN member_role TEXT DEFAULT 'leader'")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Add leader_roll_no column if missing (migration for existing DB)
    try:
        cursor.execute("ALTER TABLE participants ADD COLUMN leader_roll_no TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Add member_position column if missing (migration for existing DB)
    try:
        cursor.execute("ALTER TABLE participants ADD COLUMN member_position INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Index for faster lookup
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_roll_event ON participants(roll_no, event)")
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")

def save_participant(roll_no, name, dept, year, event, sheet_source, team_members=None):
    """
    Save participant (leader) and optionally their team members as separate records.
    
    Args:
        roll_no: Leader's roll number
        name: Leader's name
        dept: Department
        year: Year
        event: Event name
        sheet_source: Source sheet name
        team_members: List of team member names or comma-separated string
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Convert team_members to list if it's a string
    if isinstance(team_members, str):
        team_members_list = [tm.strip() for tm in team_members.split(',') if tm.strip()]
    elif isinstance(team_members, list):
        team_members_list = team_members
    else:
        team_members_list = []
    
    # Join for storage in team_members field
    team_members_str = ", ".join(team_members_list) if team_members_list else None
    
    # Upsert leader record (checking roll_no + event + member_role)
    cursor.execute("""
        SELECT id FROM participants 
        WHERE roll_no = ? AND event = ? AND member_role = 'leader'
    """, (roll_no, event))
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute("""
            UPDATE participants 
            SET name = ?, department = ?, year = ?, sheet_source = ?, team_members = ?
            WHERE id = ?
        """, (name, dept, year, sheet_source, team_members_str, existing[0]))
    else:
        cursor.execute("""
            INSERT INTO participants (roll_no, name, department, year, event, sheet_source, team_members, member_role, member_position)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'leader', 0)
        """, (roll_no, name, dept, year, event, sheet_source, team_members_str))
    
    # Delete existing team member records for this leader/event combination
    cursor.execute("""
        DELETE FROM participants 
        WHERE leader_roll_no = ? AND event = ? AND member_role = 'member'
    """, (roll_no, event))
    
    # Insert individual records for each team member
    for idx, member_name in enumerate(team_members_list, start=1):
        cursor.execute("""
            INSERT INTO participants (
                roll_no, name, department, year, event, sheet_source, 
                member_role, leader_roll_no, member_position
            ) VALUES (?, ?, ?, ?, ?, ?, 'member', ?, ?)
        """, (roll_no, member_name, dept, year, event, sheet_source, roll_no, idx))
        
    conn.commit()
    conn.close()

def get_events_for_roll(roll_no):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM participants WHERE roll_no = ?", (roll_no,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_cert_url(roll_no, event, url):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE participants SET cert_url = ? WHERE roll_no = ? AND event = ?", (url, roll_no, event))
    conn.commit()
    conn.close()

def get_all_participants():
    """Get all participants for admin view"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM participants ORDER BY event, roll_no")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def toggle_cert_visibility(participant_id, visible):
    """Toggle certificate visibility using blocked field"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Set blocked = 1 to hide, blocked = 0 to show
    blocked = 0 if visible else 1
    cursor.execute("UPDATE participants SET blocked = ? WHERE id = ?", (blocked, participant_id))
    conn.commit()
    conn.close()

def is_participant_blocked(roll_no, event):
    """Check if a participant is blocked from getting certificate"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT blocked FROM participants WHERE roll_no = ? AND event = ?", (roll_no, event))
    row = cursor.fetchone()
    conn.close()
    return row and row[0] == 1

def get_stats():
    """Get admin stats"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM participants")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT roll_no) FROM participants")
    unique_students = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT event) FROM participants")
    events = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM participants WHERE cert_url IS NOT NULL")
    certs_generated = cursor.fetchone()[0]
    
    conn.close()
    return {
        "total_records": total,
        "unique_students": unique_students,
        "events": events,
        "certs_generated": certs_generated
    }
