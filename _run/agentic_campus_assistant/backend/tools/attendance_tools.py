from typing import Optional, Dict, Any, List
from agentic_campus_assistant.backend.database.db import get_connection

def get_student_attendance(student_id: str, course_code: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve attendance records for a student.
    Calculates shortage if attendance is below 75% LPU threshold,
    and returns how many consecutive classes are needed to reach 75%.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name, section, program FROM students WHERE registration_no = ?", (student_id,))
    student_row = cursor.fetchone()
    if not student_row:
        conn.close()
        return {
            "success": False,
            "error": f"Student with registration ID '{student_id}' not found in campus directory."
        }

    student_name = student_row["name"]

    if course_code:
        cursor.execute("""
            SELECT course_code, course_name, classes_held, classes_attended, percentage
            FROM attendance
            WHERE student_id = ? AND UPPER(course_code) = UPPER(?)
        """, (student_id, course_code.strip()))
        rows = cursor.fetchall()
    else:
        cursor.execute("""
            SELECT course_code, course_name, classes_held, classes_attended, percentage
            FROM attendance
            WHERE student_id = ?
        """, (student_id,))
        rows = cursor.fetchall()

    conn.close()

    if not rows:
        return {
            "success": False,
            "error": f"No attendance records found for course '{course_code}'."
        }

    records = []
    has_warning = False
    total_held = 0
    total_attended = 0

    for r in rows:
        pct = float(r["percentage"])
        held = int(r["classes_held"])
        attended = int(r["classes_attended"])
        total_held += held
        total_attended += attended

        # Calculate needed classes for 75%:
        # (attended + x) / (held + x) >= 0.75 => x >= (0.75 * held - attended) / 0.25
        needed_for_75 = 0
        if pct < 75.0:
            has_warning = True
            needed_for_75 = max(0, int(round((0.75 * held - attended) / 0.25 + 0.49)))

        records.append({
            "course_code": r["course_code"],
            "course_name": r["course_name"],
            "classes_held": held,
            "classes_attended": attended,
            "percentage": pct,
            "status": "CRITICAL - BELOW 75%" if pct < 75.0 else ("WARNING" if pct < 80.0 else "GOOD"),
            "classes_needed_for_75": needed_for_75
        })

    overall_pct = round((total_attended / total_held * 100), 2) if total_held > 0 else 0.0

    return {
        "success": True,
        "student_id": student_id,
        "student_name": student_name,
        "overall_percentage": overall_pct,
        "records": records,
        "low_attendance_alert": has_warning,
        "action_required": "Immediate attendance remediation required to avoid exam debarment." if has_warning else "Attendance is on track."
    }
