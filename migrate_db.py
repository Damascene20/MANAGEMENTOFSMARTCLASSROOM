# migrate_db.py (Complete schema fix for Teachers table)

import sqlite3
DATABASE_NAME = 'smart_classroom.db'

conn = sqlite3.connect(DATABASE_NAME)
cursor = conn.cursor()

print(f"Connecting to {DATABASE_NAME} to update Teachers table...")

# Helper function to execute ALTER TABLE safely
def add_column_if_not_exists(column_name, definition):
    try:
        cursor.execute(f"ALTER TABLE Teachers ADD COLUMN {column_name} {definition}")
        print(f"Column '{column_name}' added successfully.")
    except sqlite3.OperationalError as e:
        # Check for the common "duplicate column name" error
        if 'duplicate column name' in str(e):
            print(f"Column '{column_name}' already exists. Skipping.")
        else:
            print(f"Error adding {column_name} column: {e}")

# 1. Add Username column (Fixes the "no such column: Username" error)
# This is required for logging in and registering.
add_column_if_not_exists('Username', 'TEXT')

# 2. Add Password column (Required for storing the user's password)
# NOTE: In production, this should be a hashed password.
add_column_if_not_exists('Password', 'TEXT')

# 3. Add Role column (Fixes the previous "no such column: Role" error)
# Default role for existing users will be 'Teacher'.
add_column_if_not_exists('Role', "TEXT DEFAULT 'Teacher'")

# 4. Add IsApproved column (Fixes the previous "no such column: IsApproved" error)
# Default status is 0 (Pending approval).
add_column_if_not_exists('IsApproved', "INTEGER DEFAULT 0")


# Commit changes and close
conn.commit()
conn.close()
print("Database schema migration for Teachers table complete. You can now run app.py.")