import random
from datetime import datetime
from typing import Optional, Dict, Any
from agentic_campus_assistant.backend.database.db import get_connection

def escalate_to_human_admin(
    student_id: str,
    user_query: str,
    reason: str,
    severity: str = "Medium",
    department: str = "Academic Affairs & Student Grievances"
) -> Dict[str, Any]:
    """
    Escalate an ambiguous, sensitive, policy-restricted, or unresolved request
    to human campus administration.
    Generates an official Escalation Ticket and notifies the duty officer.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM students WHERE registration_no = ?", (student_id,))
    student_row = cursor.fetchone()
    student_name = student_row["name"] if student_row else "Campus Student"

    ticket_id = f"ESC-{random.randint(1000, 9999)}"
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO escalation_tickets (
            ticket_id, student_id, student_name, user_query, reason,
            severity, assigned_department, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'ESCALATED_TO_ADMIN', ?)
    """, (
        ticket_id, student_id, student_name, user_query, reason,
        severity, department, created_at
    ))

    conn.commit()
    conn.close()

    contact_hotline = "+91 1824 517000 (Campus Administration Desk)"

    return {
        "success": True,
        "escalated": True,
        "ticket_id": ticket_id,
        "student_name": student_name,
        "assigned_department": department,
        "severity": severity,
        "reason": reason,
        "status": "ESCALATED_TO_ADMIN",
        "action_taken": f"This request requires human oversight. Ticket #{ticket_id} has been dispatched to {department}.",
        "contact_hotline": contact_hotline,
        "message": f"I've escalated your case to {department} (Ticket #{ticket_id}). An administrator will review your query within 2-4 working hours."
    }
