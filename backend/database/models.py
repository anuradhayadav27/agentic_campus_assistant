from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class Student(BaseModel):
    registration_no: str
    name: str
    section: str
    program: str = "B.Tech Computer Science & Engineering"
    email: str
    attendance_percentage: float

class AttendanceRecord(BaseModel):
    course_code: str
    course_name: str
    classes_held: int
    classes_attended: int
    percentage: float
    status: str  # Safe, Warning, Critical (< 75%)
    classes_needed_for_75: int

class LabSlot(BaseModel):
    slot_id: str
    lab_id: str
    lab_name: str
    building: str
    date: str
    time_range: str
    capacity: int
    available_seats: int
    hardware_specs: str
    status: str  # AVAILABLE, BOOKED, MAINTENANCE

class LabBookingRequest(BaseModel):
    student_id: str
    student_name: str
    lab_id: str
    date: str
    time_range: str
    purpose: str

class LabBookingRecord(BaseModel):
    booking_id: str
    student_id: str
    student_name: str
    lab_id: str
    date: str
    time_range: str
    purpose: str
    status: str
    created_at: str

class MaintenanceComplaintRequest(BaseModel):
    student_id: str
    student_name: str
    facility_type: str
    block: str
    room_no: str
    issue_category: str
    description: str
    priority: str = "Medium"

class MaintenanceRecord(BaseModel):
    complaint_id: str
    student_id: str
    student_name: str
    facility_type: str
    block: str
    room_no: str
    issue_category: str
    description: str
    priority: str
    status: str
    assigned_technician: str
    created_at: str

class LeaveRequest(BaseModel):
    student_id: str
    student_name: str
    leave_type: str  # Duty Leave, Medical Leave, Casual Leave
    from_date: str
    to_date: str
    reason: str
    emergency_contact: str

class LeaveRecord(BaseModel):
    leave_id: str
    student_id: str
    student_name: str
    leave_type: str
    from_date: str
    to_date: str
    total_days: int
    reason: str
    status: str
    approval_authority: str
    created_at: str

class LibraryBook(BaseModel):
    book_id: str
    title: str
    author: str
    category: str
    isbn: str
    total_copies: int
    available_copies: int
    shelf_location: str

class LibraryReservationRecord(BaseModel):
    reservation_id: str
    student_id: str
    book_id: str
    book_title: str
    shelf_location: str
    pickup_deadline: str
    loan_duration_days: int
    status: str
    created_at: str

class EscalationTicket(BaseModel):
    ticket_id: str
    student_id: str
    student_name: str
    user_query: str
    reason: str
    severity: str  # Low, Medium, High, Critical
    assigned_department: str
    status: str
    created_at: str

class AgentStepTrace(BaseModel):
    step_number: int
    step_goal: str
    tool_name: str
    tool_input: Dict[str, Any]
    tool_output: Dict[str, Any]
    status: str  # SUCCESS, FAILED, RE_PLANNED
    re_plan_note: Optional[str] = None

class AgentExecutionTrace(BaseModel):
    request_id: str
    user_query: str
    intent: str
    decomposed_subgoals: List[str]
    steps: List[AgentStepTrace]
    final_response: str
    execution_time_ms: float
    escalated: bool = False
    escalation_ticket_id: Optional[str] = None
    comparison_with_rule_based: Optional[Dict[str, Any]] = None
