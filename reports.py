# reports.py

from db_setup import connect_db

def get_teacher_ranking():
    """Ranks teachers by the number of approved bookings (use)."""
    conn = connect_db()
    cursor = conn.cursor()
    
    query = """
    SELECT 
        T.Name, 
        COUNT(B.BookingID) AS UsageCount
    FROM Bookings B
    JOIN Teachers T ON B.TeacherID = T.TeacherID
    WHERE B.Status = 'Approved'
    GROUP BY T.Name
    ORDER BY UsageCount DESC
    """
    
    cursor.execute(query)
    ranking = cursor.fetchall()
    conn.close()
    
    print("\n--- Teacher Usage Ranking (By Approved Bookings) ---")
    if ranking:
        print("Rank | Teacher Name | Times Used")
        print("-----|--------------|-----------")
        for i, (name, count) in enumerate(ranking, 1):
            print(f"{i:<4} | {name:<12} | {count}")
    else:
        print("No approved bookings yet.")
    
    return ranking

def get_subject_ranking():
    """Ranks subjects by the number of approved bookings (use)."""
    conn = connect_db()
    cursor = conn.cursor()
    
    query = """
    SELECT 
        T.Subject, 
        COUNT(B.BookingID) AS SubjectUsageCount
    FROM Bookings B
    JOIN Teachers T ON B.TeacherID = T.TeacherID
    WHERE B.Status = 'Approved'
    GROUP BY T.Subject
    ORDER BY SubjectUsageCount DESC
    """
    
    cursor.execute(query)
    ranking = cursor.fetchall()
    conn.close()
    
    print("\n--- Subject Usage Ranking (By Approved Bookings) ---")
    if ranking:
        print("Rank | Subject | Times Used")
        print("-----|---------|-----------")
        for i, (subject, count) in enumerate(ranking, 1):
            print(f"{i:<4} | {subject:<7} | {count}")
    else:
        print("No approved bookings yet.")
        
    return ranking

def get_status_summary():
    """Provides a count of approved, pending, and denied bookings."""
    conn = connect_db()
    cursor = conn.cursor()
    
    query = """
    SELECT Status, COUNT(*) 
    FROM Bookings 
    GROUP BY Status
    """
    
    cursor.execute(query)
    summary = dict(cursor.fetchall())
    conn.close()
    
    print("\n--- Booking Status Summary ---")
    print(f"Total Approved Bookings: {summary.get('Approved', 0)}")
    print(f"Total Pending Bookings: {summary.get('Pending', 0)}")
    print(f"Total Denied Bookings: {summary.get('Denied', 0)}")
    
    return summary

# Example usage when running this script:
if __name__ == '__main__':
    # You must run smart_scheduler.py first to generate bookings!
    get_teacher_ranking()
    get_subject_ranking()
    get_status_summary()