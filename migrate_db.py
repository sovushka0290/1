import sqlite3
import os

db_path = "/home/aqtobe-hub/ProtoQol/protoqol_mvp.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cols = [
    ("plan_type", "TEXT DEFAULT 'Free'"), 
    ("credits_total", "INTEGER DEFAULT 10"), 
    ("credits_used", "INTEGER DEFAULT 0"), 
    ("expires_at", "TIMESTAMP DEFAULT (datetime('now', '+30 days'))")
]

for col, col_type in cols:
    try:
        cursor.execute(f"ALTER TABLE clients ADD COLUMN {col} {col_type};")
        print(f"Added column {col}")
    except sqlite3.OperationalError:
        print(f"Column {col} already exists")

conn.commit()
conn.close()
print("Migration complete.")
