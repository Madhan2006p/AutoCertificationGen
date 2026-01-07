import sqlite3

def init_db():
    conn = sqlite3.connect("forms_data.db")
    cursor = conn.cursor()
    
    # 1. Create settings table for maintenance mode
    cursor.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('maintenance', 'false')")
    
    # 2. Add 'generating' and 'cert_url' columns to participants
    cursor.execute("PRAGMA table_info(participants)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if "generating" not in columns:
        print("Adding 'generating' column...")
        cursor.execute("ALTER TABLE participants ADD COLUMN generating INTEGER DEFAULT 0")
        
    if "cert_url" not in columns:
        print("Adding 'cert_url' column...")
        cursor.execute("ALTER TABLE participants ADD COLUMN cert_url TEXT")
    
    conn.commit()
    conn.close()
    print("✅ Database hardening complete.")

if __name__ == "__main__":
    init_db()
