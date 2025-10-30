# show_tables_with_data.py
from db_setup import connect_db

def show_tables_with_data():
    conn = connect_db()
    if not conn:
        print("Cannot connect to the database.")
        return

    cursor = conn.cursor()

    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    if not tables:
        print("No tables found in the database.")
        return

    for table in tables:
        table_name = table[0]
        print(f"\n{'='*50}\nTable: {table_name}\n{'='*50}")

        # Get columns for the table
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        print("Columns:", ", ".join(column_names))

        # Get all data
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        if rows:
            print("\nData:")
            for row in rows:
                row_data = ", ".join(str(item) for item in row)
                print(row_data)
        else:
            print("\nNo data in this table.")

    conn.close()

if __name__ == "__main__":
    show_tables_with_data()
