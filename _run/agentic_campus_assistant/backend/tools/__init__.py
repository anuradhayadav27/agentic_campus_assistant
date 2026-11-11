from typing import Dict, Any, Callable
from agentic_campus_assistant.backend.tools.attendance_tools import get_student_attendance
from agentic_campus_assistant.backend.tools.lab_tools import check_lab_availability, book_lab_slot
from agentic_campus_assistant.backend.tools.maintenance_tools import file_maintenance_complaint, check_complaint_status
from agentic_campus_assistant.backend.tools.leave_tools import submit_leave_application, check_leave_status
from agentic_campus_assistant.backend.tools.library_tools import search_library_books, reserve_library_book
from agentic_campus_assistant.backend.tools.escalation_tools import escalate_to_human_admin

CAMPUS_TOOL_DEFINITIONS = [
    {
        "name": "get_student_attendance",
        "description": "Check a student's current attendance records, percentage by course, and identify attendance shortage below the 75% LPU threshold with remediation steps.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {"type": "string", "description": "Student registration number (e.g. 12109482)"},
                "course_code": {"type": "string", "description": "Optional course code such as 'CSE276', 'INT306'"}
            },
            "required": ["student_id"]
        }
    },
    {
        "name": "check_lab_availability",
        "description": "Query available lab seats and time slots across university computer and AI labs for a given date.",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Date in YYYY-MM-DD or 'tomorrow'/'today'"},
                "lab_id": {"type": "string", "description": "Optional lab ID like 'LAB-34-601'"},
                "preferred_time": {"type": "string", "description": "Optional time like '11:00' or '09:00'"}
            }
        }
    },
    {
        "name": "book_lab_slot",
        "description": "Reserve a seat in a campus laboratory. If full, triggers re-planning by returning closest alternatives.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {"type": "string", "description": "Student registration number"},
                "lab_id": {"type": "string", "description": "Laboratory ID (e.g. 'LAB-34-601')"},
                "date": {"type": "string", "description": "Date of booking (YYYY-MM-DD or 'tomorrow')"},
                "time_range": {"type": "string", "description": "Time slot range (e.g. '11:00 - 13:00')"},
                "purpose": {"type": "string", "description": "Purpose of lab access"}
            },
            "required": ["student_id", "lab_id", "date", "time_range"]
        }
    },
    {
        "name": "file_maintenance_complaint",
        "description": "Log an infrastructure issue (projector, AC, electrical, LAN, PC) in a campus classroom or lab and dispatch to technical teams.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {"type": "string", "description": "Student registration number"},
                "facility_type": {"type": "string", "description": "Classroom, Lab, Hostel, or Library"},
                "block": {"type": "string", "description": "Campus block (e.g. 'Block 34')"},
                "room_no": {"type": "string", "description": "Room or lab number (e.g. 'Room 601')"},
                "issue_category": {"type": "string", "description": "Category (Projector, Air Conditioning, Electrical, Internet/LAN, Computer/Hardware)"},
                "description": {"type": "string", "description": "Specific issue details"},
                "priority": {"type": "string", "enum": ["Low", "Medium", "High", "Critical"], "description": "Urgency"}
            },
            "required": ["student_id", "block", "room_no", "issue_category", "description"]
        }
    },
    {
        "name": "check_complaint_status",
        "description": "Check current status and assigned technician of existing maintenance tickets.",
        "parameters": {
            "type": "object",
            "properties": {
                "complaint_id": {"type": "string", "description": "Complaint ID (e.g. 'CMP-8012')"},
                "student_id": {"type": "string", "description": "Student registration ID"}
            }
        }
    },
    {
        "name": "submit_leave_application",
        "description": "Submit a leave application (Duty, Medical, Casual) with automated policy verification.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {"type": "string", "description": "Student registration number"},
                "leave_type": {"type": "string", "description": "Medical Leave, Duty Leave, or Casual Leave"},
                "from_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                "to_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
                "reason": {"type": "string", "description": "Reason for leave"}
            },
            "required": ["student_id", "leave_type", "from_date", "to_date", "reason"]
        }
    },
    {
        "name": "check_leave_status",
        "description": "Check status of submitted leave applications for a student.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {"type": "string", "description": "Student registration number"}
            },
            "required": ["student_id"]
        }
    },
    {
        "name": "search_library_books",
        "description": "Search the university central library catalog for textbooks, authors, and shelf locations.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Book title or keywords"},
                "category": {"type": "string", "description": "Subject category"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "reserve_library_book",
        "description": "Hold and reserve a book in the campus library for student collection.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {"type": "string", "description": "Student registration number"},
                "book_id": {"type": "string", "description": "Book ID or exact title"}
            },
            "required": ["student_id", "book_id"]
        }
    },
    {
        "name": "escalate_to_human_admin",
        "description": "Escalate to human university administration when request involves confidential disputes, grade changes, policy appeals, or unresolved failures.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {"type": "string", "description": "Student registration number"},
                "user_query": {"type": "string", "description": "The original user query"},
                "reason": {"type": "string", "description": "Why automated handling is insufficient"},
                "severity": {"type": "string", "enum": ["Low", "Medium", "High", "Critical"]},
                "department": {"type": "string", "description": "Target office (e.g. 'Academic Appeals Committee')"}
            },
            "required": ["student_id", "user_query", "reason"]
        }
    }
]

TOOL_REGISTRY: Dict[str, Callable] = {
    "get_student_attendance": get_student_attendance,
    "check_lab_availability": check_lab_availability,
    "book_lab_slot": book_lab_slot,
    "file_maintenance_complaint": file_maintenance_complaint,
    "check_complaint_status": check_complaint_status,
    "submit_leave_application": submit_leave_application,
    "check_leave_status": check_leave_status,
    "search_library_books": search_library_books,
    "reserve_library_book": reserve_library_book,
    "escalate_to_human_admin": escalate_to_human_admin
}
