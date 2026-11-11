import random
from datetime import datetime
from typing import Optional, Dict, Any, List
from agentic_campus_assistant.backend.database.db import get_connection

def submit_leave_application(
    student_id: str,
    leave_type: str,
    from_date: str,
    to_date: str,
    reason: str,
    emergency_contact: Optional[str] = None
) -> Dict[str, Any]:
    """
    Submit a student leave application for academic or residential absence.
    Validates institutional leave rules, calculates days, and routes to appropriate authority.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name, hostel_block, phone FROM students WHERE registration_no = ?", (student_id,))
    student_row = cursor.fetchone()
    if not student_row:
        conn.close()
        return {"success": False, "error": f"Student with ID '{student_id}' not found."}

    student_name = student_row["name"]
    hostel = student_row["hostel_block"]

    # Calculate days difference if formatted YYYY-MM-DD
    total_days = 1
    try:
        d1 = datetime.strptime(from_date, "%Y-%m-%d")
        d2 = datetime.strptime(to_date, "%Y-%m-%d")
        total_days = max(1, (d2 - d1).days + 1)
    except Exception:
        total_days = 1

    # Institutional policy checks
    policy_notes = []
    normalized_type = leave_type.title()

    if "Medical" in normalized_type:
        approval_authority = "Chief Medical Officer & Academic Dean"
        if total_days > 2:
            policy_notes.append("Medical leave exceeding 2 days requires doctor's fitness prescription upon campus return.")
    elif "Duty" in normalized_type:
        approval_authority = "Head of Department (CSE) & Faculty Coordinator"
        policy_notes.append("Duty leave counts towards attendance upon certificate verification.")
    else:
        approval_authority = f"Hostel Warden ({hostel}) & Proctor"
        if total_days > 4:
            policy_notes.append("Casual leave > 4 days requires parental verification via SMS/call.")

    leave_id = f"LEV-{random.randint(1000, 9999)}"
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO leave_applications (
            leave_id, student_id, student_name, leave_type, from_date, to_date,
            total_days, reason, status, approval_authority, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pending Approval', ?, ?)
    """, (
        leave_id, student_id, student_name, normalized_type, from_date, to_date,
        total_days, reason, approval_authority, created_at
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "leave_id": leave_id,
        "student_name": student_name,
        "leave_type": normalized_type,
        "from_date": from_date,
        "to_date": to_date,
        "total_days": total_days,
        "reason": reason,
        "status": "Pending Approval",
        "routed_to": approval_authority,
        "policy_alerts": policy_notes,
        "message": f"Leave application #{leave_id} successfully registered and forwarded to {approval_authority}."
    }

def check_leave_status(student_id: str) -> Dict[str, Any]:
    """
    Retrieve history and current review status of leave applications for a student.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT leave_id, leave_type, from_date, to_date, total_days, reason, status, approval_authority, created_at
        FROM leave_applications
        WHERE student_id = ?
        ORDER BY created_at DESC
    """, (student_id.strip(),))

    rows = cursor.fetchall()
    conn.close()

    records = []
    for r in rows:
        records.append({
            "leave_id": r["leave_id"],
            "leave_type": r["leave_type"],
            "duration": f"{r['from_date']} to {r['to_date']} ({r['total_days']} days)",
            "reason": r["reason"],
            "status": r["status"],
            "authority": r["approval_authority"],
            "applied_on": r["created_at"]
        })

    return {
        "success": True,
        "student_id": student_id,
        "total_applications": len(records),
        "applications": records
    }
