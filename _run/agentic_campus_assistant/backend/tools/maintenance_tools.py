import random
from datetime import datetime
from typing import Optional, Dict, Any, List
from agentic_campus_assistant.backend.database.db import get_connection

TECHNICIAN_MAPPING = {
    "Projector": "Rajesh Sharma (Audio-Visual Systems Support)",
    "Air Conditioning": "Vikram Singh (HVAC Engineering Team)",
    "Electrical": "Manoj Kumar (Campus Electrical Division)",
    "Internet/LAN": "Pooja Verma (IT Network & Fiber Operations)",
    "Furniture": "Ramesh Patel (Campus Estate Maintenance)",
    "Computer/Hardware": "Gurpreet Singh (Lab Systems Administrator)",
    "General": "Central Campus Estate Helpdesk"
}

def file_maintenance_complaint(
    student_id: str,
    block: str,
    room_no: str,
    issue_category: str,
    description: str,
    facility_type: str = "Classroom",
    priority: str = "Medium"
) -> Dict[str, Any]:
    """
    File a campus facility maintenance complaint.
    Automatically assigns an appropriate technician team and generates a trackable Ticket ID.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM students WHERE registration_no = ?", (student_id,))
    student_row = cursor.fetchone()
    student_name = student_row["name"] if student_row else "Campus Student"

    # Match technician team
    assigned_technician = TECHNICIAN_MAPPING.get(issue_category, TECHNICIAN_MAPPING["General"])
    for key in TECHNICIAN_MAPPING:
        if key.lower() in issue_category.lower() or key.lower() in description.lower():
            assigned_technician = TECHNICIAN_MAPPING[key]
            break

    complaint_id = f"CMP-{random.randint(1000, 9999)}"
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO maintenance_complaints (
            complaint_id, student_id, student_name, facility_type, block, room_no,
            issue_category, description, priority, status, assigned_technician, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Open', ?, ?)
    """, (
        complaint_id, student_id, student_name, facility_type, block, room_no,
        issue_category, description, priority, assigned_technician, created_at
    ))

    conn.commit()
    conn.close()

    # SLA resolution estimate
    sla_hours = 4 if priority.lower() in ["high", "critical"] else 24

    return {
        "success": True,
        "complaint_id": complaint_id,
        "student_name": student_name,
        "location": f"{facility_type} in {block}, Room {room_no}",
        "issue_category": issue_category,
        "description": description,
        "priority": priority,
        "status": "Open",
        "assigned_technician": assigned_technician,
        "estimated_resolution_time": f"Within {sla_hours} hours",
        "message": f"Maintenance ticket #{complaint_id} dispatched to {assigned_technician}."
    }

def check_complaint_status(complaint_id: Optional[str] = None, student_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Query existing campus maintenance complaints by ticket ID or student ID.
    """
    conn = get_connection()
    cursor = conn.cursor()

    if complaint_id:
        cursor.execute("SELECT * FROM maintenance_complaints WHERE complaint_id = ?", (complaint_id.strip(),))
    elif student_id:
        cursor.execute("SELECT * FROM maintenance_complaints WHERE student_id = ? ORDER BY created_at DESC", (student_id.strip(),))
    else:
        cursor.execute("SELECT * FROM maintenance_complaints ORDER BY created_at DESC LIMIT 5")

    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "complaint_id": r["complaint_id"],
            "student_name": r["student_name"],
            "facility_type": r["facility_type"],
            "location": f"{r['block']}, Room {r['room_no']}",
            "issue_category": r["issue_category"],
            "description": r["description"],
            "priority": r["priority"],
            "status": r["status"],
            "assigned_technician": r["assigned_technician"],
            "created_at": r["created_at"]
        })

    return {
        "success": True,
        "total_records": len(results),
        "complaints": results
    }
