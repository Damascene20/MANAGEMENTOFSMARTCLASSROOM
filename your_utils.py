import sqlite3

DB_FILE = "smart_classroom.db"

def ensure_system_settings_table():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS SystemSettings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_duration INTEGER DEFAULT 40,
        lab_status TEXT DEFAULT 'Available'
    )
    """)
    conn.commit()
    conn.close()
import sqlite3

conn = sqlite3.connect("smart_classroom.db")
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(Bookings);")
columns = cursor.fetchall()
conn.close()

for col in columns:
    print(col)
