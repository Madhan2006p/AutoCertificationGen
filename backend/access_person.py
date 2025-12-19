import pandas as pd
import genCertificate as gc
import sqlite3

conn = sqlite3.connect("forms_data.db")

def get_user_by_reg(reg):
    query = """
        SELECT * 
        FROM participants 
        WHERE roll_no = ?
"""
    df = pd.read_sql_query(query , conn , params=(reg, ))
    for _, row in df.iterrows():
        gc.generate_certificate(
            name=row["name"],
            roll_no=row["roll_no"],
            event=row["event"]
        )
    conn.close()
    print(df)



