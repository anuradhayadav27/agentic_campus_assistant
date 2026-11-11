import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "campus.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Students
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        registration_no TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        section TEXT NOT NULL,
        program TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        hostel_block TEXT NOT NULL,
        room_no TEXT NOT NULL
    )
    """)

    # 2. Attendance
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        course_code TEXT NOT NULL,
        course_name TEXT NOT NULL,
        classes_held INTEGER NOT NULL,
        classes_attended INTEGER NOT NULL,
        percentage REAL NOT NULL,
        FOREIGN KEY(student_id) REFERENCES students(registration_no)
    )
    """)

    # 3. Labs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS labs (
        lab_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        building TEXT NOT NULL,
        floor TEXT NOT NULL,
        capacity INTEGER NOT NULL,
        hardware_specs TEXT NOT NULL
    )
    """)

    # 4. Lab Slots
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lab_slots (
        slot_id TEXT PRIMARY KEY,
        lab_id TEXT NOT NULL,
        date TEXT NOT NULL,
        time_range TEXT NOT NULL,
        available_seats INTEGER NOT NULL,
        status TEXT NOT NULL, -- AVAILABLE, FULL, MAINTENANCE
        FOREIGN KEY(lab_id) REFERENCES labs(lab_id)
    )
    """)

    # 5. Lab Bookings
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lab_bookings (
        booking_id TEXT PRIMARY KEY,
        student_id TEXT NOT NULL,
        student_name TEXT NOT NULL,
        lab_id TEXT NOT NULL,
        date TEXT NOT NULL,
        time_range TEXT NOT NULL,
        purpose TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    # 6. Maintenance Complaints
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS maintenance_complaints (
        complaint_id TEXT PRIMARY KEY,
        student_id TEXT NOT NULL,
        student_name TEXT NOT NULL,
        facility_type TEXT NOT NULL,
        block TEXT NOT NULL,
        room_no TEXT NOT NULL,
        issue_category TEXT NOT NULL,
        description TEXT NOT NULL,
        priority TEXT NOT NULL,
        status TEXT NOT NULL,
        assigned_technician TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    # 7. Leave Applications
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leave_applications (
        leave_id TEXT PRIMARY KEY,
        student_id TEXT NOT NULL,
        student_name TEXT NOT NULL,
        leave_type TEXT NOT NULL,
        from_date TEXT NOT NULL,
        to_date TEXT NOT NULL,
        total_days INTEGER NOT NULL,
        reason TEXT NOT NULL,
        status TEXT NOT NULL,
        approval_authority TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    # 8. Library Books
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS library_books (
        book_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        category TEXT NOT NULL,
        isbn TEXT NOT NULL,
        total_copies INTEGER NOT NULL,
        available_copies INTEGER NOT NULL,
        shelf_location TEXT NOT NULL
    )
    """)

    # 9. Library Reservations
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS library_reservations (
        reservation_id TEXT PRIMARY KEY,
        student_id TEXT NOT NULL,
        book_id TEXT NOT NULL,
        book_title TEXT NOT NULL,
        shelf_location TEXT NOT NULL,
        pickup_deadline TEXT NOT NULL,
        loan_duration_days INTEGER NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    # 10. Escalation Tickets
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS escalation_tickets (
        ticket_id TEXT PRIMARY KEY,
        student_id TEXT NOT NULL,
        student_name TEXT NOT NULL,
        user_query TEXT NOT NULL,
        reason TEXT NOT NULL,
        severity TEXT NOT NULL,
        assigned_department TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    # 11. Execution Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS execution_logs (
        log_id TEXT PRIMARY KEY,
        student_id TEXT NOT NULL,
        user_query TEXT NOT NULL,
        intent TEXT NOT NULL,
        decomposed_plan TEXT NOT NULL,
        steps_executed TEXT NOT NULL,
        final_response TEXT NOT NULL,
        execution_time_ms REAL NOT NULL,
        escalated INTEGER NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    conn.commit()
    seed_initial_data(conn)
    conn.close()

def seed_initial_data(conn):
    cursor = conn.cursor()

    # Check if data exists
    cursor.execute("SELECT COUNT(*) FROM students")
    if cursor.fetchone()[0] > 0:
        return

    # Seed Students (Group 9 members)
    students = [
        ("12109482", "Anupa Yadav", "K4P25", "B.Tech CSE - AI & ML", "anupa.yadav@lpu.in", "+91 98765 43210", "BH-4", "412"),
        ("12109483", "Ruben Jose", "K4P25", "B.Tech CSE - AI & ML", "ruben.jose@lpu.in", "+91 98765 43211", "BH-4", "413"),
        ("12109484", "Erick Simon Kasole", "K4P25", "B.Tech CSE - AI & ML", "erick.kasole@lpu.in", "+91 98765 43212", "BH-4", "414"),
    ]
    cursor.executemany("INSERT INTO students VALUES (?, ?, ?, ?, ?, ?, ?, ?)", students)

    # Seed Attendance (Notice: CSE276 is slightly below 75% for Anupa to showcase intelligent warnings!)
    attendance = [
        # Anupa Yadav
        ("12109482", "CSE276", "Artificial Intelligence Foundations", 40, 28, 70.0), # Critical / Below 75%
        ("12109482", "INT306", "Cloud Computing Architectures", 36, 32, 88.89),
        ("12109482", "CSE325", "Operating Systems & Concurrency", 42, 34, 80.95),
        ("12109482", "MTH401", "Applied Probability & Statistics", 30, 26, 86.67),

        # Ruben Jose
        ("12109483", "CSE276", "Artificial Intelligence Foundations", 40, 33, 82.5),
        ("12109483", "INT306", "Cloud Computing Architectures", 36, 30, 83.33),
        ("12109483", "CSE325", "Operating Systems & Concurrency", 42, 31, 73.81), # Low
        ("12109483", "MTH401", "Applied Probability & Statistics", 30, 27, 90.0),

        # Erick Simon Kasole
        ("12109484", "CSE276", "Artificial Intelligence Foundations", 40, 36, 90.0),
        ("12109484", "INT306", "Cloud Computing Architectures", 36, 26, 72.22), # Low
        ("12109484", "CSE325", "Operating Systems & Concurrency", 42, 35, 83.33),
        ("12109484", "MTH401", "Applied Probability & Statistics", 30, 28, 93.33),
    ]
    cursor.executemany("""
    INSERT INTO attendance (student_id, course_code, course_name, classes_held, classes_attended, percentage)
    VALUES (?, ?, ?, ?, ?, ?)
    """, attendance)

    # Seed Labs
    labs = [
        ("LAB-34-601", "Advanced AI & GPU Computing Lab", "Block 34", "6th Floor", 45, "30x NVIDIA RTX 4090, 64GB RAM, Ubuntu 24.04, PyTorch/TensorFlow"),
        ("LAB-34-602", "Robotics & Embedded Systems Lab", "Block 34", "6th Floor", 40, "ROS2 Nodes, Jetson Orin Nano, Arduino/Raspberry Pi"),
        ("LAB-38-301", "Apple Developer & iOS Lab", "Block 38", "3rd Floor", 50, "50x Apple Mac Mini M2 Pro, Xcode, Swift 5.9"),
        ("LAB-36-204", "Cloud & High Performance Computing Lab", "Block 36", "2nd Floor", 60, "Dell Precision Workstations, OpenStack, Docker/K8s cluster"),
    ]
    cursor.executemany("INSERT INTO labs VALUES (?, ?, ?, ?, ?, ?)", labs)

    # Seed Dynamic Slots for Today and Tomorrow
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    day_after = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")

    slots = [
        # Today slots
        ("SLOT-34-601-T1", "LAB-34-601", today, "09:00 - 11:00", 12, "AVAILABLE"),
        ("SLOT-34-601-T2", "LAB-34-601", today, "11:00 - 13:00", 0, "FULL"), # Full slot to demonstrate replanning
        ("SLOT-34-601-T3", "LAB-34-601", today, "14:00 - 16:00", 18, "AVAILABLE"),

        # Tomorrow slots
        ("SLOT-34-601-TM1", "LAB-34-601", tomorrow, "09:00 - 11:00", 0, "FULL"), # Demonstrates conflict handling
        ("SLOT-34-601-TM2", "LAB-34-601", tomorrow, "11:00 - 13:00", 15, "AVAILABLE"),
        ("SLOT-34-601-TM3", "LAB-34-601", tomorrow, "14:00 - 16:00", 25, "AVAILABLE"),

        # LAB-34-602 slots tomorrow
        ("SLOT-34-602-TM1", "LAB-34-602", tomorrow, "09:00 - 11:00", 8, "AVAILABLE"),
        ("SLOT-34-602-TM2", "LAB-34-602", tomorrow, "11:00 - 13:00", 20, "AVAILABLE"),

        # LAB-38-301 Mac Lab
        ("SLOT-38-301-TM1", "LAB-38-301", tomorrow, "10:00 - 12:00", 22, "AVAILABLE"),
        ("SLOT-38-301-TM2", "LAB-38-301", tomorrow, "14:00 - 16:00", 19, "AVAILABLE"),

        # Day after tomorrow
        ("SLOT-34-601-DA1", "LAB-34-601", day_after, "10:00 - 12:00", 30, "AVAILABLE"),
    ]
    cursor.executemany("INSERT INTO lab_slots VALUES (?, ?, ?, ?, ?, ?)", slots)

    # Seed Library Books
    books = [
        ("LIB-BK-101", "Artificial Intelligence: A Modern Approach (4th Ed)", "Stuart Russell & Peter Norvig", "Artificial Intelligence", "978-0134610993", 10, 4, "Central Library - 2nd Floor, Shelf AI-04"),
        ("LIB-BK-102", "Deep Learning", "Ian Goodfellow, Yoshua Bengio, Aaron Courville", "Deep Learning", "978-0262035613", 8, 2, "Central Library - 2nd Floor, Shelf DL-01"),
        ("LIB-BK-103", "Reinforcement Learning: An Introduction", "Richard S. Sutton & Andrew G. Barto", "Machine Learning", "978-0262039246", 6, 0, "Central Library - 2nd Floor, Shelf RL-02"), # 0 copies to test waitlist/re-planning!
        ("LIB-BK-104", "Designing Data-Intensive Applications", "Martin Kleppmann", "Cloud & Systems", "978-1449373320", 12, 7, "Central Library - 3rd Floor, Shelf SYS-11"),
        ("LIB-BK-105", "Operating System Concepts (10th Ed)", "Abraham Silberschatz, Peter Galvin", "Systems Software", "978-1118063330", 15, 9, "Central Library - 1st Floor, Shelf OS-08"),
        ("LIB-BK-106", "Pattern Recognition and Machine Learning", "Christopher M. Bishop", "Data Science", "978-0387310732", 7, 3, "Central Library - 2nd Floor, Shelf ML-05"),
    ]
    cursor.executemany("INSERT INTO library_books VALUES (?, ?, ?, ?, ?, ?, ?, ?)", books)

    # Seed Sample Complaints
    complaints = [
        ("CMP-8012", "12109482", "Anupa Yadav", "Classroom", "Block 34", "Room 601", "Projector", "HDMI display flickering and turning black intermittently", "High", "In Progress", "Rajesh Sharma (AV Support)", (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M")),
        ("CMP-7940", "12109483", "Ruben Jose", "Lab", "Block 38", "Room 301", "Air Conditioning", "AC Unit #2 blowing warm air", "Medium", "Resolved", "Vikram Singh (HVAC Team)", (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d %H:%M")),
    ]
    cursor.executemany("INSERT INTO maintenance_complaints VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", complaints)

    # Seed Sample Leave Applications
    leaves = [
        ("LEV-4019", "12109482", "Anupa Yadav", "Duty Leave", (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"), (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d"), 2, "Attending Smart India Hackathon zonal round", "Approved", "Dr. HOD Computer Science", (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")),
    ]
    cursor.executemany("INSERT INTO leave_applications VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", leaves)

    conn.commit()

def reset_db():
    conn = get_connection()
    cursor = conn.cursor()
    tables = [
        "students", "attendance", "labs", "lab_slots", "lab_bookings",
        "maintenance_complaints", "leave_applications", "library_books",
        "library_reservations", "escalation_tickets", "execution_logs"
    ]
    for t in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {t}")
    conn.commit()
    conn.close()
    init_db()

if __name__ == "__main__":
    init_db()
    print("Campus Database initialized and seeded successfully at:", DB_PATH)
