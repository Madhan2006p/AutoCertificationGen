import pandas as pd
import sqlite3

conn = sqlite3.connect("forms_data.db")

def get_user_by_reg(reg):
    query = """
        SELECT * 
        FROM participants 
        WHERE roll_no = ?
"""
    df = pd.read_sql_query(query , conn , params=(reg, ))

    conn.close()
    print(df)



