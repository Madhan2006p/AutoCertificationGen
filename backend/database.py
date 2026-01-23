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
            cert_url TEXT
        )
    """)
    
    # Index for faster lookup
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_roll_event ON participants(roll_no, event)")
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")

def save_participant(roll_no, name, dept, year, event, sheet_source):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Upsert logic (checking roll_no + event)
    cursor.execute("SELECT id FROM participants WHERE roll_no = ? AND event = ?", (roll_no, event))
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute("""
            UPDATE participants 
            SET name = ?, department = ?, year = ?, sheet_source = ?
            WHERE id = ?
        """, (name, dept, year, sheet_source, existing[0]))
    else:
        cursor.execute("""
            INSERT INTO participants (roll_no, name, department, year, event, sheet_source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (roll_no, name, dept, year, event, sheet_source))
        
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
    cursor.execute("SELECT * FROM participants ORDER BY roll_no, event")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def toggle_cert_visibility(participant_id, visible):
    """Toggle certificate visibility (clear or restore cert_url)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if not visible:
        # Hide: backup URL to a temp field and clear cert_url
        cursor.execute("UPDATE participants SET cert_url = NULL WHERE id = ?", (participant_id,))
    conn.commit()
    conn.close()

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
