import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from agentic_campus_assistant.backend.database.db import init_db
from agentic_campus_assistant.backend.agent.core_agent import CampusAgenticAI
from agentic_campus_assistant.backend.agent.rule_based_baseline import RuleBasedCampusChatbot
from agentic_campus_assistant.backend.tools.attendance_tools import get_student_attendance
from agentic_campus_assistant.backend.tools.lab_tools import check_lab_availability, book_lab_slot
from agentic_campus_assistant.backend.tools.maintenance_tools import file_maintenance_complaint
from agentic_campus_assistant.backend.tools.leave_tools import submit_leave_application
from agentic_campus_assistant.backend.tools.library_tools import search_library_books, reserve_library_book
from agentic_campus_assistant.backend.tools.escalation_tools import escalate_to_human_admin
from agentic_campus_assistant.backend.main import app

def test_attendance_tool():
    res = get_student_attendance("12109482", "CSE276")
    assert res["success"] is True
    assert res["student_name"] == "Anupa Yadav"
    assert len(res["records"]) == 1
    rec = res["records"][0]
    assert rec["course_code"] == "CSE276"
    assert rec["percentage"] == 70.0
    assert rec["classes_needed_for_75"] > 0

def test_maintenance_complaint_tool():
    res = file_maintenance_complaint(
        student_id="12109483",
        block="Block 34",
        room_no="Room 601",
        issue_category="Projector",
        description="Flickering HDMI connection",
        priority="High"
    )
    assert res["success"] is True
    assert "CMP-" in res["complaint_id"]
    assert res["status"] == "Open"
    assert "Rajesh Sharma" in res["assigned_technician"]

def test_leave_application_policy_check():
    res = submit_leave_application(
        student_id="12109482",
        leave_type="Medical Leave",
        from_date="2026-11-12",
        to_date="2026-11-16",
        reason="Viral fever and high temperature"
    )
    assert res["success"] is True
    assert res["total_days"] >= 4
    assert len(res["policy_alerts"]) > 0
    assert "Medical leave exceeding 2 days" in res["policy_alerts"][0]

def test_library_reservation_and_replanning_candidate():
    res = search_library_books("Artificial Intelligence")
    assert res["success"] is True
    assert res["books_found"] > 0

    reserve_res = reserve_library_book("12109482", "LIB-BK-101")
    assert reserve_res["success"] is True
    assert "LIB-" in reserve_res["reservation_id"]

def test_agent_multi_intent_goal_decomposition():
    agent = CampusAgenticAI()
    query = "Check my attendance for CSE276, and book Lab 34-601 for tomorrow at 11 AM."
    result = agent.process_request(query, "12109482")

    assert result["total_subgoals"] >= 2
    assert len(result["steps"]) >= 2
    assert result["succeeded_subgoals"] >= 2
    assert "Attendance" in result["final_response"]
    assert "Lab Booking" in result["final_response"]

def test_agent_dynamic_replanning_on_conflict():
    agent = CampusAgenticAI()
    query = "Book Lab 34-601 tomorrow for 09:00 - 11:00 slot."
    result = agent.process_request(query, "12109482")

    assert len(result["steps"]) > 0
    step = result["steps"][0]
    assert step["status"] == "RE_PLANNED_SUCCESS" or "Re-Planned" in step["status"]

def test_agent_human_escalation():
    agent = CampusAgenticAI()
    query = "I was falsely accused of disciplinary cheating and I demand an official grievance hearing."
    result = agent.process_request(query, "12109483")

    assert result["escalated"] is True
    assert result["escalation_ticket_id"] is not None
    assert "ESC-" in result["escalation_ticket_id"]

def test_rule_based_comparison_difference():
    agent = CampusAgenticAI()
    rule_engine = RuleBasedCampusChatbot()
    compound_query = "What is my attendance in CSE276 and submit a complaint about broken projector in Room 601"

    agent_res = agent.process_request(compound_query, "12109482")
    rule_res = rule_engine.process(compound_query, "12109482")

    assert agent_res["total_subgoals"] >= 2
    assert agent_res["succeeded_subgoals"] >= 2
    assert rule_res["multi_step_supported"] is False
    assert rule_res["subgoals_completed"] == 1

def test_fastapi_endpoints():
    client = TestClient(app)
    r = client.get('/api/health')
    assert r.status_code == 200
    assert "Group 9" in r.json()["group"]

    r = client.get('/api/services/data?student_id=12109482')
    assert r.status_code == 200
    assert len(r.json()["students"]) == 3

    r = client.post('/api/chat', json={'message': 'Check attendance in CSE276', 'student_id': '12109482'})
    assert r.status_code == 200
    assert "attendance" in r.json()["final_response"].lower()
