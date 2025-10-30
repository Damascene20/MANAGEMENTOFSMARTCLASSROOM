# smart_scheduler.py

from datetime import datetime, timedelta
from db_setup import connect_db # Using the connect_db from db_setup
import sqlite3 
DB_FILE = "smart_classroom.db"
# --- CONFIGURATION ---
# Note: BOOKING_DURATION_MINUTES is often pulled from SystemSettings now, 
# but kept here as a fallback or default.

BOOKING_DURATION_MINUTES = 40 

# --- SCHEMA MIGRATION / UTILITY FUNCTIONS ---

def _check_and_add_column(conn, table_name, column_name, column_type="TEXT", default_value=None):
    """A safe, reusable function to check and add a column if it's missing."""
    cursor = conn.cursor()
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        
        if column_name not in columns:
            default_clause = f" DEFAULT '{default_value}'" if default_value is not None else ""
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}{default_clause}")
            conn.commit()
            print(f"Database Updated: Successfully added '{column_name}' column to {table_name} table. ✅")

    except sqlite3.OperationalError as e:
        # Ignore errors if the table doesn't exist (handled by db_setup.py)
        if "no such table" not in str(e):
             print(f"Error during table migration for {table_name}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during migration: {e}")


def run_database_migrations():
    """Runs all necessary database schema updates."""
    try:
        conn = connect_db()
        if conn:
            # Teachers table migrations
            _check_and_add_column(conn, "Teachers", "Email", "TEXT")
            _check_and_add_column(conn, "Teachers", "Phone", "TEXT")
            _check_and_add_column(conn, "Teachers", "Class", "TEXT")
            _check_and_add_column(conn, "Teachers", "IsApproved", "INTEGER", default_value=0) 

            # Bookings table migrations
            _check_and_add_column(conn, "Bookings", "Equipment", "TEXT")
            
        else:
            print("Could not connect to the database for migrations.")
    except Exception as e:
        print(f"Error running database migrations: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

# --- TIME UTILITIES ---

def calculate_end_time(start_time_str, duration=BOOKING_DURATION_MINUTES):
    """Calculates the end time based on a given duration."""
    try:
        # Fetch actual duration from settings if available, otherwise use default
        try:
            duration = int(get_system_setting('session_duration') or duration)
        except:
            duration = BOOKING_DURATION_MINUTES

        start_dt = datetime.strptime(start_time_str, '%H:%M')
        end_dt = start_dt + timedelta(minutes=duration) 
        return end_dt.strftime('%H:%M')
    except ValueError:
        return None

def is_working_hours(start_time_str):
    """Checks if the request is between 8:00 AM and 5:00 PM (17:00)."""
    try:
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        start_limit = datetime.strptime('08:00', '%H:%M').time()
        end_limit = datetime.strptime('17:00', '%H:%M').time()
        return start_limit <= start_time < end_limit
    except ValueError:
        return False

def get_available_hours():
    """Generates a list of all possible 40-minute slots from 8:00 AM to 5:00 PM."""
    # Fetch duration from settings
    try:
        duration = int(get_system_setting('session_duration') or BOOKING_DURATION_MINUTES)
    except:
        duration = BOOKING_DURATION_MINUTES

    available_times = []
    start_time_str = '08:00'
    end_time_limit_str = '17:00'
    current_dt = datetime.strptime(start_time_str, '%H:%M')
    end_limit_dt = datetime.strptime(end_time_limit_str, '%H:%M')

    while current_dt + timedelta(minutes=duration) <= end_limit_dt:
        time_slot = current_dt.strftime('%H:%M')
        display_slot = f"{time_slot} - {calculate_end_time(time_slot, duration)}"
        available_times.append((time_slot, display_slot))
        current_dt += timedelta(minutes=duration) 
        
    return available_times


# --- BOOKING FUNCTIONS ---

def check_availability(room_id, date_str, start_time_str):
    """Checks if the room is available for the booking period on a specific date."""
    end_time_str = calculate_end_time(start_time_str)
    
    if not end_time_str or not is_working_hours(start_time_str):
        return False

    conn = connect_db()
    cursor = conn.cursor()

    # Overlap Logic: checks if (StartA < EndB) AND (EndA > StartB)
    query = """
    SELECT COUNT(*) FROM Bookings
    WHERE RoomID = ?
      AND Date = ?
      AND Status IN ('Pending', 'Approved')
      AND (
          (StartTime < ? AND EndTime > ?)
      )
    """
    cursor.execute(query, (room_id, date_str, end_time_str, start_time_str))
    
    count = cursor.fetchone()[0]
    conn.close()

    return count == 0

def submit_booking_request(teacher_id, room_id, date_str, start_time_str, equipment):
    """Submits a request, checking availability."""
    
    if not check_availability(room_id, date_str, start_time_str):
        return False

    end_time_str = calculate_end_time(start_time_str)
    
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO Bookings 
            (TeacherID, RoomID, Date, StartTime, EndTime, Equipment, Status) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (teacher_id, room_id, date_str, start_time_str, end_time_str, equipment, 'Pending'))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"ERROR submitting booking: {e}") 
        return False
    finally:
        conn.close()

def update_booking_status(booking_id, new_status):
    """Updates the status of a specific booking (e.g., 'Approved' or 'Denied')."""
    if new_status not in ['Approved', 'Denied', 'Cancelled']:
        return False
        
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Bookings SET Status = ? WHERE BookingID = ?", 
                       (new_status, booking_id))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Database error updating booking status: {e}")
        return False
    finally:
        conn.close()

def get_pending_requests():
    """Retrieves all pending booking requests for the ICT Teacher view."""
    conn = connect_db()
    cursor = conn.cursor()
    query = """
    SELECT b.BookingID, t.Name AS Teacher, c.Name AS Room, b.Date, b.StartTime, b.Equipment 
    FROM Bookings b
    JOIN Teachers t ON b.TeacherID = t.TeacherID
    JOIN Classrooms c ON b.RoomID = c.RoomID
    WHERE b.Status = 'Pending'
    ORDER BY b.Date, b.StartTime
    """
    cursor.execute(query)
    requests = cursor.fetchall()
    conn.close()
    return requests
    
def get_bookings_by_teacher_id(teacher_id):
    """Retrieves all past, pending, and future bookings for a specific teacher."""
    conn = connect_db()
    cursor = conn.cursor()
    query = """
    SELECT 
        B.BookingID, 
        R.Name AS RoomName, 
        B.Date, 
        B.StartTime, 
        B.EndTime,
        B.Status, 
        B.Equipment 
    FROM Bookings B
    JOIN Classrooms R ON B.RoomID = R.RoomID
    WHERE B.TeacherID = ?
    ORDER BY B.Date DESC, B.StartTime DESC
    """
    cursor.execute(query, (teacher_id,))
    bookings = cursor.fetchall()
    conn.close()
    return bookings

def get_all_approved_bookings():
    """Retrieves all approved bookings (for calendar/overview purposes)."""
    conn = connect_db()
    cursor = conn.cursor()
    query = """
    SELECT 
        B.BookingID, 
        T.Name AS TeacherName,
        R.Name AS RoomName, 
        B.Date, 
        B.StartTime,
        B.EndTime
    FROM Bookings B
    JOIN Teachers T ON B.TeacherID = T.TeacherID
    JOIN Classrooms R ON B.RoomID = R.RoomID
    WHERE B.Status = 'Approved'
    ORDER BY B.Date ASC, B.StartTime ASC
    """
    cursor.execute(query)
    all_bookings = cursor.fetchall()
    conn.close()
    return all_bookings


# --- TEACHER/ADMIN FUNCTIONS ---
# All return raw database tuples.

def get_teacher_by_username(username):
    """Retrieves a teacher's record by username for login."""
    conn = connect_db()
    cursor = conn.cursor()
    # Returns (TeacherID, Name, Subject, Username, Password, Role, IsApproved, Email, Phone, Class)
    query = "SELECT TeacherID, Name, Subject, Username, Password, Role, IsApproved, Email, Phone, Class FROM Teachers WHERE Username = ?"
    cursor.execute(query, (username,))
    teacher = cursor.fetchone()
    conn.close()
    return teacher 
    
def get_teacher_by_id(teacher_id):
    """Retrieves a teacher's record by ID."""
    conn = connect_db()
    cursor = conn.cursor()
    # Returns (TeacherID, Name, Subject, Username, Password, Role, IsApproved, Email, Phone, Class)
    query = "SELECT TeacherID, Name, Subject, Username, Password, Role, IsApproved, Email, Phone, Class FROM Teachers WHERE TeacherID = ?"
    cursor.execute(query, (teacher_id,))
    teacher = cursor.fetchone()
    conn.close()
    return teacher 

def register_ict_admin(name, username, password):
    """Registers a user with the ICT_Admin role and automatically approves them."""
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT TeacherID FROM Teachers WHERE Username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return "Username already exists."

    try:
        cursor.execute(
            """
            INSERT INTO Teachers (Name, Subject, Username, Password, Role, IsApproved)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, "ICT Administration", username, password, 'ICT_Admin', 1)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error registering admin: {e}")
        return False
    finally:
        conn.close()
    
def update_teacher_approval_status(teacher_id, new_status):
    """Updates the IsApproved status for a teacher (1 for Approved, 0 for Pending/Denied)."""
    status_value = 1 if str(new_status) == '1' else 0
    
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Teachers SET IsApproved = ? WHERE TeacherID = ?", 
                       (status_value, teacher_id))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"DB Error updating teacher approval: {e}")
        return False
    finally:
        conn.close()
    
def delete_teacher_by_id(teacher_id):
    """Deletes a teacher and their associated bookings."""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        # Prevent deleting the primary admin account if logic dictates
        cursor.execute("SELECT Role FROM Teachers WHERE TeacherID = ?", (teacher_id,))
        role = cursor.fetchone()
        if role and role[0] == 'ICT_Admin':
            return False # Prevent deletion

        cursor.execute("DELETE FROM Bookings WHERE TeacherID = ?", (teacher_id,))
        cursor.execute("DELETE FROM Teachers WHERE TeacherID = ?", (teacher_id,))
        conn.commit()
        return True 
    except sqlite3.Error as e:
        print(f"Database error deleting teacher: {e}")
        return False
    finally:
        conn.close() 

def get_all_teacher_management_data():
    """Retrieves ALL essential data from the Teachers table for administrative viewing."""
    conn = connect_db()
    cursor = conn.cursor()
    query = """
    SELECT 
        TeacherID, Name, Subject, Username, Role, IsApproved, Email, Phone, Class
    FROM Teachers
    ORDER BY IsApproved ASC, Name ASC;
    """
    try:
        cursor.execute(query)
        teachers_data = cursor.fetchall()
        return teachers_data
    except sqlite3.Error as e:
        print(f"Database error fetching teacher management data: {e}")
        return []
    finally:
        conn.close()


# --- ROOM AND REPORT FUNCTIONS ---

def get_all_rooms():
    """Returns a list of all rooms as tuples (RoomID, RoomName)."""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT RoomID, Name FROM Classrooms ORDER BY Name")
        rooms = cursor.fetchall()
        return [(room[0], room[1]) for room in rooms]
    except sqlite3.Error as e:
        print(f"Database error fetching rooms: {e}")
        return []
    finally:
        conn.close()

def get_usage_reports_and_summary():
    """Retrieves data required for the reports dashboard."""
    conn = connect_db()
    cursor = conn.cursor()
    
    # 1. Teacher Usage Ranking (Approved Only)
    teacher_query = """
    SELECT T.Name, COUNT(B.BookingID) AS Count
    FROM Bookings B
    JOIN Teachers T ON B.TeacherID = T.TeacherID
    WHERE B.Status = 'Approved'
    GROUP BY T.Name
    ORDER BY Count DESC
    """
    cursor.execute(teacher_query)
    teacher_ranking = cursor.fetchall()

    # 2. Subject Usage Ranking (Approved Only)
    subject_query = """
    SELECT T.Subject, COUNT(B.BookingID) AS Count
    FROM Bookings B
    JOIN Teachers T ON B.TeacherID = T.TeacherID
    WHERE B.Status = 'Approved'
    GROUP BY T.Subject
    ORDER BY Count DESC
    """
    cursor.execute(subject_query)
    subject_ranking = cursor.fetchall()
    
    # 3. Overall Booking Status Summary
    summary_query = """
    SELECT Status, COUNT(BookingID) AS Count
    FROM Bookings
    GROUP BY Status
    """
    cursor.execute(summary_query)
    summary_data = cursor.fetchall()
    
    conn.close()
    
    summary_dict = {status: count for status, count in summary_data}
    
    return teacher_ranking, subject_ranking, summary_dict 

# --- SYSTEM SETTINGS FUNCTIONS ---

def get_system_setting(key):
    """Retrieves a single system setting value by key."""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT Value FROM SystemSettings WHERE Key = ?", (key,))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.OperationalError as e:
        # Happens if the table hasn't been created yet
        return None
    finally:
        conn.close()

def update_system_setting(key, value):
    """Inserts or updates a single system setting key-value pair."""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO SystemSettings (Key, Value)
            VALUES (?, ?)
        """, (key, value))
        conn.commit()
    except sqlite3.OperationalError as e:
        print(f"Error updating SystemSettings table: {e}")
    finally:
        conn.close()
        # smart_scheduler.py (Add this function)

# smart_scheduler.py

def get_all_bookings():
    """
    Retrieves all bookings from the database, joining with Teacher and Classroom names.
    """
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            B.BookingID, B.Date, B.StartTime, B.EndTime, B.Equipment, B.Status,
            T.Name AS TeacherName, T.Subject, 
            C.Name AS ClassroomName
        FROM Bookings B
        JOIN Teachers T ON B.TeacherID = T.TeacherID
        JOIN Classrooms C ON B.RoomID = C.RoomID   -- ✅ Corrected
        ORDER BY B.Date DESC, B.StartTime DESC
    """)
    
    bookings = cursor.fetchall()
    conn.close()
    return bookings
# smart_scheduler.py
# smart_scheduler.py (Hypothetically)

# smart_scheduler.py (Fix: Ensure it uses the function that sets the row_factory)

def get_all_classrooms():
    # If connect_db is the function that sets conn.row_factory = sqlite3.Row
    conn = connect_db() 
    if not conn:
        return []
        
    cursor = conn.cursor()
    
    cursor.execute("SELECT ClassroomID, Name, Capacity FROM Classrooms")
    
    all_classrooms = cursor.fetchall()
    
    conn.close()
    # 'all_classrooms' will now contain data accessible by name, e.g., row['Name']
    return all_classrooms

def get_db_connection():
    """Returns a SQLite connection with row_factory set to sqlite3.Row."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row # <--- THIS IS REQUIRED
    return conn

# smart_scheduler.py

def get_all_teachers():
    """Retrieves all records from the Teachers table."""
    conn = connect_db()
    
    # Check 1: Connection failure
    if not conn:
        return []
        
    teachers = []
    try:
        cursor = conn.cursor()
        
        # 1. Execute the SELECT * query
        cursor.execute("SELECT * FROM Teachers")
        
        # 2. Fetch all results (If row_factory is set, this returns dictionary-like objects)
        teachers = cursor.fetchall()
        
    except Exception as e:
        # Handle exceptions during query execution (e.g., table not found)
        print(f"Database error fetching teachers: {e}")
        teachers = [] # Ensure we return an empty list on failure
        
    finally:
        # Ensure the connection is closed whether or not an error occurred
        conn.close()
        
    return teachers