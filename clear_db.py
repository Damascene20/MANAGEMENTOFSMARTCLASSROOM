import sqlite3

DB_PATH = "smart_classroom.db"  # Path to your database file

def clear_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if sqlite_sequence exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='sqlite_sequence';
    """)
    has_sequence = cursor.fetchone() is not None

    # Fetch all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    print("🧹 Clearing all tables in smart_classroom.db...\n")

    for (table_name,) in tables:
        if table_name.startswith('sqlite_'):  # Skip system tables
            continue

        print(f"Deleting all data from table: {table_name}")
        cursor.execute(f"DELETE FROM {table_name};")

        # Reset AUTOINCREMENT only if sqlite_sequence exists
        if has_sequence:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name=?;", (table_name,))

    conn.commit()
    conn.close()
    print("\n✅ All data in 'smart_classroom' database has been cleared successfully!")

if __name__ == "__main__":
    clear_database()
