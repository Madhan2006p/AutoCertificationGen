import pandas as pd
from backend.genCertificate import generate_certificate
import sqlite3



def get_user_by_reg(reg):
    conn = sqlite3.connect("forms_data.db")
    query = """
        SELECT * 
        FROM participants 
        WHERE roll_no = ?
"""
    df = pd.read_sql_query(query , conn , params=(reg, ))
    for _, row in df.iterrows():
        generate_certificate(
            name=row["name"],
            roll_no=row["roll_no"],
            event=row["event"]
        )
    conn.close()
    return df



