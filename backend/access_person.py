import pandas as pd
import sqlite3

def get_user_by_reg(reg):
    """
    Fetch user data by registration number (roll_no).
    Does NOT generate certificates synchronously to avoid blocking.
    """
    conn = sqlite3.connect("forms_data.db")
    
    # Check if cert_url column exists, add if not
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT cert_url FROM participants LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE participants ADD COLUMN cert_url TEXT")
        conn.commit()

    query = """
        SELECT * 
        FROM participants 
        WHERE roll_no = ?
    """
    df = pd.read_sql_query(query, conn, params=(reg,))
    conn.close()
    return df
