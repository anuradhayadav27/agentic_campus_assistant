import random
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from agentic_campus_assistant.backend.database.db import get_connection

def check_lab_availability(date: Optional[str] = None, lab_id: Optional[str] = None, preferred_time: Optional[str] = None) -> Dict[str, Any]:
    """
    Check available slots across campus computer and AI labs.
    If date is not specified, defaults to tomorrow.
    """
    if not date or date.lower() in ["tomorrow", "tmrw"]:
        date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    elif date.lower() in ["today"]:
        date = datetime.now().strftime("%Y-%m-%d")

    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT s.slot_id, s.lab_id, l.name as lab_name, l.building, l.hardware_specs, s.date, s.time_range, s.available_seats, s.status
        FROM lab_slots s
        JOIN labs l ON s.lab_id = l.lab_id
        WHERE s.date = ?
    """
    params = [date]

    if lab_id:
        query += " AND UPPER(s.lab_id) LIKE UPPER(?)"
        params.append(f"%{lab_id.strip()}%")

    if preferred_time:
        query += " AND s.time_range LIKE ?"
        params.append(f"%{preferred_time.strip()}%")

    query += " ORDER BY s.time_range ASC"

    cursor.execute(query, params)
    rows = cursor.fetchall()

    slots = []
    for r in rows:
        slots.append({
            "slot_id": r["slot_id"],
            "lab_id": r["lab_id"],
            "lab_name": r["lab_name"],
            "building": r["building"],
            "hardware_specs": r["hardware_specs"],
            "date": r["date"],
            "time_range": r["time_range"],
            "available_seats": r["available_seats"],
            "status": r["status"]
        })

    conn.close()

    available_slots = [s for s in slots if s["status"] == "AVAILABLE" and s["available_seats"] > 0]

    return {
        "success": True,
        "date_queried": date,
        "total_slots_found": len(slots),
        "available_slots_count": len(available_slots),
        "slots": slots,
        "has_available": len(available_slots) > 0
    }

def book_lab_slot(student_id: str, lab_id: str, date: str, time_range: str, purpose: str = "Academic Research / AI Practical") -> Dict[str, Any]:
    """
    Book a slot in a campus laboratory.
    If the requested slot is full, returns failure status with alternative suggestions
    so that the Agentic AI can re-plan.
    """
    if not date or date.lower() in ["tomorrow", "tmrw"]:
        date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    elif date.lower() in ["today"]:
        date = datetime.now().strftime("%Y-%m-%d")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM students WHERE registration_no = ?", (student_id,))
    student_row = cursor.fetchone()
    student_name = student_row["name"] if student_row else "Student"

    # Find slot
    cursor.execute("""
        SELECT slot_id, available_seats, status, lab_id
        FROM lab_slots
        WHERE date = ? AND (lab_id LIKE ? OR lab_id = ?) AND time_range LIKE ?
    """, (date, f"%{lab_id}%", lab_id, f"%{time_range}%"))
    slot_row = cursor.fetchone()

    # Slot check
    if not slot_row:
        # Check any slot on that date for this lab
        cursor.execute("SELECT slot_id, time_range, available_seats, status FROM lab_slots WHERE date = ? AND lab_id LIKE ?", (date, f"%{lab_id}%"))
        alt_rows = cursor.fetchall()
        conn.close()

        alternatives = [{"time_range": a["time_range"], "available_seats": a["available_seats"], "status": a["status"]} for a in alt_rows if a["status"] == "AVAILABLE"]
        return {
            "success": False,
            "error_type": "SLOT_NOT_FOUND",
            "message": f"Exact slot '{time_range}' not scheduled for {lab_id} on {date}.",
            "suggested_alternatives": alternatives
        }

    if slot_row["status"] != "AVAILABLE" or slot_row["available_seats"] <= 0:
        # Look for alternative slots on the same date
        cursor.execute("""
            SELECT s.slot_id, s.lab_id, l.name as lab_name, s.time_range, s.available_seats
            FROM lab_slots s
            JOIN labs l ON s.lab_id = l.lab_id
            WHERE s.date = ? AND s.status = 'AVAILABLE' AND s.available_seats > 0
        """, (date,))
        alternatives = [
            {"lab_id": r["lab_id"], "lab_name": r["lab_name"], "time_range": r["time_range"], "available_seats": r["available_seats"]}
            for r in cursor.fetchall()
        ]
        conn.close()

        return {
            "success": False,
            "error_type": "SLOT_FULL_CONFLICT",
            "message": f"Requested slot '{time_range}' in {lab_id} on {date} is currently FULL (0 seats available).",
            "suggested_alternatives": alternatives
        }

    # Book slot
    booking_id = f"LBK-{random.randint(1000, 9999)}"
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Update slot seats
    new_seats = slot_row["available_seats"] - 1
    new_status = "AVAILABLE" if new_seats > 0 else "FULL"
    cursor.execute("UPDATE lab_slots SET available_seats = ?, status = ? WHERE slot_id = ?", (new_seats, new_status, slot_row["slot_id"]))

    # Insert booking
    cursor.execute("""
        INSERT INTO lab_bookings (booking_id, student_id, student_name, lab_id, date, time_range, purpose, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'CONFIRMED', ?)
    """, (booking_id, student_id, student_name, slot_row["lab_id"], date, time_range, purpose, created_at))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "booking_id": booking_id,
        "student_id": student_id,
        "student_name": student_name,
        "lab_id": slot_row["lab_id"],
        "date": date,
        "time_range": time_range,
        "purpose": purpose,
        "status": "CONFIRMED",
        "remaining_seats": new_seats,
        "instructions": f"Bring your university ID card to {slot_row['lab_id']}. Booking passes automatically to campus turnstiles."
    }
