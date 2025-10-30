# db_setup.py
import sqlite3

DB_FILE = "smart_classroom.db"

def connect_db():
    """Connects to the SQLite database and returns the connection object."""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = None 
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None

def initialize_database():
    """
    Creates the necessary tables if they do not exist.
    This runs once at the very start of the application lifecycle.
    """
    conn = connect_db()
    if not conn:
        print("FATAL: Cannot initialize database due to connection error.")
        return

    cursor = conn.cursor()
    try:
        # Teachers Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Teachers (
                TeacherID INTEGER PRIMARY KEY AUTOINCREMENT,
                Name TEXT NOT NULL,
                Subject TEXT,
                Username TEXT UNIQUE NOT NULL,
                Password TEXT NOT NULL,
                Role TEXT DEFAULT 'Teacher',
                IsApproved INTEGER DEFAULT 0,
                Email TEXT,
                Phone TEXT,
                Class TEXT
            )
        """)

        # Classrooms Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Classrooms (
                RoomID INTEGER PRIMARY KEY AUTOINCREMENT,
                Name TEXT UNIQUE NOT NULL,
                EquipmentList TEXT
            )
        """)
        # Insert default rooms if none exist
        default_rooms = [
            ('SMART Lab 1', 'Interactive Whiteboard, Projector, 30 PCs'),
            ('SMART Lab 2', 'Projector, 25 Laptops'),
            ('Meeting Room A', 'Interactive Display, Video Conferencing Equipment')
        ]
        for name, equipment in default_rooms:
            cursor.execute("INSERT OR IGNORE INTO Classrooms (Name, EquipmentList) VALUES (?, ?)", (name, equipment))

        # Bookings Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Bookings (
                BookingID INTEGER PRIMARY KEY AUTOINCREMENT,
                TeacherID INTEGER NOT NULL,
                RoomID INTEGER NOT NULL,
                Date TEXT NOT NULL,
                StartTime TEXT NOT NULL,
                EndTime TEXT NOT NULL,
                Equipment TEXT,
                Status TEXT DEFAULT 'Pending',
                FOREIGN KEY (TeacherID) REFERENCES Teachers(TeacherID),
                FOREIGN KEY (RoomID) REFERENCES Classrooms(RoomID)
            )
        """)

        # System Settings Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS SystemSettings (
                Key TEXT PRIMARY KEY,
                Value TEXT NOT NULL
            )
        """)
        # Insert default settings
        cursor.execute("INSERT OR IGNORE INTO SystemSettings VALUES ('session_duration', '40')")
        cursor.execute("INSERT OR IGNORE INTO SystemSettings VALUES ('lab_status', 'Available')")
        cursor.execute("INSERT OR IGNORE INTO SystemSettings VALUES ('booking_cutoff_minutes', '40')")

        # ----------- MaterialRequests Table -----------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS MaterialRequests (
                RequestID INTEGER PRIMARY KEY AUTOINCREMENT,
                FullName TEXT NOT NULL,
                Gender TEXT NOT NULL,
                PhoneNumber TEXT NOT NULL,
                ClassTeacher TEXT,
                MaterialName TEXT NOT NULL,
                BorrowedDate TEXT NOT NULL,
                ReturnedDate TEXT NOT NULL,
                Reason TEXT,
                LetterFile TEXT NOT NULL,
                Status TEXT DEFAULT 'Pending',
                CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        print("INFO: Database initialized successfully. All tables ensured.")

    except sqlite3.Error as e:
        print(f"Database initialization error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    initialize_database()
