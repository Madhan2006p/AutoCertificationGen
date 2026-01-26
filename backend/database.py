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
            team_members TEXT
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
    
    # Index for faster lookup
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_roll_event ON participants(roll_no, event)")
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")

def save_participant(roll_no, name, dept, year, event, sheet_source, team_members=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Upsert logic (checking roll_no + event)
    cursor.execute("SELECT id FROM participants WHERE roll_no = ? AND event = ?", (roll_no, event))
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute("""
            UPDATE participants 
            SET name = ?, department = ?, year = ?, sheet_source = ?, team_members = ?
            WHERE id = ?
        """, (name, dept, year, sheet_source, team_members, existing[0]))
    else:
        cursor.execute("""
            INSERT INTO participants (roll_no, name, department, year, event, sheet_source, team_members)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (roll_no, name, dept, year, event, sheet_source, team_members))
        
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
