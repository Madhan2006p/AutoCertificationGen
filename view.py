import sqlite3
import pandas as pd

# Show full text
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.width', None)

conn = sqlite3.connect("forms_data.db")

df = pd.read_sql_query(
    "SELECT * FROM form_responses", conn
)

conn.close()

print(df)
