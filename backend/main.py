import os
import json
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agentic_campus_assistant.backend.database.db import get_connection, init_db
from agentic_campus_assistant.backend.agent.core_agent import CampusAgenticAI
from agentic_campus_assistant.backend.evaluation.benchmark import run_comparative_benchmark

app = FastAPI(
    title="Agentic AI Campus Assistant",
    description="Multi-Step Autonomous Campus Service Workflows with Goal Decomposition, Dynamic Re-Planning & Scripted Baseline Comparison",
    version="1.0.0"
)

# Enable CORS for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Database on startup
init_db()
agent_instance = CampusAgenticAI()

class ChatRequest(BaseModel):
    message: str
    student_id: Optional[str] = "12109482"

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Agentic AI Campus Workflow Engine",
        "group": "Group 9 (Ruben Jose, Anupa Yadav, Erick Simon Kasole)",
        "course": "CSE276 - Artificial Intelligence Foundations"
    }

@app.post("/api/chat")
def handle_chat(req: ChatRequest):
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Query message cannot be empty.")
    try:
        response_data = agent_instance.process_request(req.message, req.student_id or "12109482")
        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent runtime error: {str(e)}")

@app.get("/api/services/data")
def get_campus_data(student_id: Optional[str] = "12109482"):
    conn = get_connection()
    cursor = conn.cursor()

    # Students
    cursor.execute("SELECT registration_no, name, section, program, email, hostel_block, room_no FROM students")
    students = [dict(r) for r in cursor.fetchall()]

    # Current student attendance
    cursor.execute("""
        SELECT course_code, course_name, classes_held, classes_attended, percentage
        FROM attendance WHERE student_id = ?
    """, (student_id,))
    attendance = [dict(r) for r in cursor.fetchall()]

    # Labs & Slots
    cursor.execute("""
        SELECT s.slot_id, s.lab_id, l.name as lab_name, l.building, s.date, s.time_range, s.available_seats, s.status, l.hardware_specs
        FROM lab_slots s
        JOIN labs l ON s.lab_id = l.lab_id
        ORDER BY s.date ASC, s.time_range ASC
    """)
    lab_slots = [dict(r) for r in cursor.fetchall()]

    # Lab Bookings
    cursor.execute("SELECT * FROM lab_bookings ORDER BY created_at DESC LIMIT 10")
    bookings = [dict(r) for r in cursor.fetchall()]

    # Maintenance Complaints
    cursor.execute("SELECT * FROM maintenance_complaints ORDER BY created_at DESC LIMIT 10")
    complaints = [dict(r) for r in cursor.fetchall()]

    # Leave Applications
    cursor.execute("SELECT * FROM leave_applications ORDER BY created_at DESC LIMIT 10")
    leaves = [dict(r) for r in cursor.fetchall()]

    # Library Books
    cursor.execute("SELECT * FROM library_books ORDER BY title ASC")
    books = [dict(r) for r in cursor.fetchall()]

    # Library Reservations
    cursor.execute("SELECT * FROM library_reservations ORDER BY created_at DESC LIMIT 10")
    reservations = [dict(r) for r in cursor.fetchall()]

    # Escalations
    cursor.execute("SELECT * FROM escalation_tickets ORDER BY created_at DESC LIMIT 10")
    escalations = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return {
        "students": students,
        "selected_student_attendance": attendance,
        "lab_slots": lab_slots,
        "recent_bookings": bookings,
        "complaints": complaints,
        "leave_applications": leaves,
        "library_books": books,
        "library_reservations": reservations,
        "escalation_tickets": escalations
    }

@app.get("/api/benchmark/run")
def run_benchmark():
    try:
        report = run_comparative_benchmark()
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmark execution error: {str(e)}")

@app.get("/api/logs")
def get_logs(limit: int = 15):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM execution_logs ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()

    logs = []
    for r in rows:
        d = dict(r)
        try:
            d["decomposed_plan"] = json.loads(d["decomposed_plan"])
            d["steps_executed"] = json.loads(d["steps_executed"])
        except Exception:
            pass
        logs.append(d)

    return {"logs": logs}

# Mount static frontend
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
