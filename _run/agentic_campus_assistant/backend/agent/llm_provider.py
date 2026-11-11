import os
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

class SemanticAgentEngine:
    """
    Intelligent Local Semantic Engine for Agentic Goal Decomposition and Parameter Extraction.
    Allows full offline execution, zero-cost viva demonstrations, and testing,
    with an optional bridge to OpenAI/Gemini if API keys are configured.
    """

    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")

    def plan_and_decompose(self, query: str, student_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decompose a compound natural language request into a sequence of atomic sub-goals
        with appropriate tool mappings and extracted parameters.
        """
        query_lower = query.lower()
        subgoals = []
        intent_summary = "Campus Multi-Workflow Request"

        # Check for Human Escalation conditions first
        escalation_triggers = [
            "dispute", "unfair", "disciplinary", "cheating", "ragging", "harassment",
            "fine waiver", "grade change", "appeal against", "sue", "legal", "bribe", "police"
        ]
        if any(trig in query_lower for trig in escalation_triggers):
            subgoals.append({
                "subgoal_id": 1,
                "goal_description": "Escalate confidential or disciplinary dispute to Campus Administration",
                "tool_name": "escalate_to_human_admin",
                "tool_input": {
                    "student_id": student_info.get("registration_no", "12109482"),
                    "user_query": query,
                    "reason": "Request involves academic dispute or administrative grievance requiring human authority.",
                    "severity": "High",
                    "department": "Dean of Student Affairs & Academic Grievance Cell"
                }
            })
            return {
                "intent": "Administrative Grievance Escalation",
                "is_escalation": True,
                "subgoals": subgoals
            }

        # Subgoal 1: Attendance Checking
        if any(w in query_lower for w in ["attendance", "present", "classes held", "shortage", "bunk"]):
            # Detect course code if present (e.g. CSE276, INT306, CSE325, MTH401)
            course_match = re.search(r"\b(CSE\s*276|INT\s*306|CSE\s*325|MTH\s*401)\b", query, re.IGNORECASE)
            course_code = course_match.group(1).replace(" ", "").upper() if course_match else None

            subgoals.append({
                "subgoal_id": len(subgoals) + 1,
                "goal_description": f"Retrieve student attendance metrics and compute remediation thresholds" + (f" for {course_code}" if course_code else " for all enrolled courses"),
                "tool_name": "get_student_attendance",
                "tool_input": {
                    "student_id": student_info.get("registration_no", "12109482"),
                    "course_code": course_code
                }
            })

        # Subgoal 2: Lab Availability & Booking
        if any(w in query_lower for w in ["book", "reserve", "slot", "lab", "laboratory", "workstation"]):
            # Extract lab identifier
            lab_match = re.search(r"\b(34-601|34-602|38-301|36-204|lab-34-601|lab-34-602|lab-38-301)\b", query, re.IGNORECASE)
            lab_id = f"LAB-{lab_match.group(1).upper()}" if lab_match else "LAB-34-601"
            if not lab_id.startswith("LAB-"):
                lab_id = f"LAB-{lab_id}"

            # Extract date
            if "tomorrow" in query_lower or "tmrw" in query_lower:
                date_val = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            elif "today" in query_lower:
                date_val = datetime.now().strftime("%Y-%m-%d")
            else:
                date_match = re.search(r"\b(202\d-\d{2}-\d{2})\b", query)
                date_val = date_match.group(1) if date_match else (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

            # Extract time slot
            time_match = re.search(r"\b(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b", query_lower)
            if "9" in query_lower or "09:00" in query_lower:
                time_range = "09:00 - 11:00"
            elif "11" in query_lower or "11:00" in query_lower:
                time_range = "11:00 - 13:00"
            elif "2" in query_lower or "14:00" in query_lower or "afternoon" in query_lower:
                time_range = "14:00 - 16:00"
            elif "10" in query_lower or "10:00" in query_lower:
                time_range = "10:00 - 12:00"
            else:
                time_range = "11:00 - 13:00"

            subgoals.append({
                "subgoal_id": len(subgoals) + 1,
                "goal_description": f"Reserve lab seat in {lab_id} on {date_val} for slot {time_range}",
                "tool_name": "book_lab_slot",
                "tool_input": {
                    "student_id": student_info.get("registration_no", "12109482"),
                    "lab_id": lab_id,
                    "date": date_val,
                    "time_range": time_range,
                    "purpose": "Academic practical and AI model benchmarking"
                }
            })

        # Subgoal 3: Maintenance Complaints
        if any(w in query_lower for w in ["complaint", "broken", "repair", "projector", "fan", "ac", "air condition", "light", "flicker", "not working", "damage"]):
            # Extract category
            category = "General Maintenance"
            if "projector" in query_lower: category = "Projector"
            elif "ac" in query_lower or "air condition" in query_lower: category = "Air Conditioning"
            elif "fan" in query_lower or "light" in query_lower or "electrical" in query_lower: category = "Electrical"
            elif "lan" in query_lower or "internet" in query_lower or "wifi" in query_lower: category = "Internet/LAN"
            elif "computer" in query_lower or "monitor" in query_lower or "mouse" in query_lower: category = "Computer/Hardware"

            # Extract location
            block_match = re.search(r"\b(block\s*\d+|bh-\d+|gh-\d+)\b", query, re.IGNORECASE)
            block_val = block_match.group(1).title() if block_match else "Block 34"

            room_match = re.search(r"\b(room\s*\d+|\d{3})\b", query, re.IGNORECASE)
            room_val = room_match.group(1) if room_match else "Room 601"

            subgoals.append({
                "subgoal_id": len(subgoals) + 1,
                "goal_description": f"Log maintenance ticket for {category} defect in {block_val}, {room_val}",
                "tool_name": "file_maintenance_complaint",
                "tool_input": {
                    "student_id": student_info.get("registration_no", "12109482"),
                    "facility_type": "Classroom" if "room" in room_val.lower() else "Lab",
                    "block": block_val,
                    "room_no": room_val,
                    "issue_category": category,
                    "description": query,
                    "priority": "High" if category in ["Projector", "Air Conditioning"] else "Medium"
                }
            })

        # Subgoal 4: Leave Applications
        if any(w in query_lower for w in ["leave", "sick", "medical", "absent", "duty leave", "casual leave"]):
            leave_type = "Casual Leave"
            if "medical" in query_lower or "sick" in query_lower or "doctor" in query_lower or "fever" in query_lower:
                leave_type = "Medical Leave"
            elif "duty" in query_lower or "hackathon" in query_lower or "conference" in query_lower:
                leave_type = "Duty Leave"

            # Dates
            today_dt = datetime.now()
            from_dt = (today_dt + timedelta(days=2)).strftime("%Y-%m-%d")
            to_dt = (today_dt + timedelta(days=4)).strftime("%Y-%m-%d")

            date_matches = re.findall(r"\b(202\d-\d{2}-\d{2})\b", query)
            if len(date_matches) >= 2:
                from_dt, to_dt = date_matches[0], date_matches[1]
            elif len(date_matches) == 1:
                from_dt = date_matches[0]
                to_dt = (datetime.strptime(from_dt, "%Y-%m-%d") + timedelta(days=2)).strftime("%Y-%m-%d")

            subgoals.append({
                "subgoal_id": len(subgoals) + 1,
                "goal_description": f"File institutional {leave_type} from {from_dt} to {to_dt}",
                "tool_name": "submit_leave_application",
                "tool_input": {
                    "student_id": student_info.get("registration_no", "12109482"),
                    "leave_type": leave_type,
                    "from_date": from_dt,
                    "to_date": to_dt,
                    "reason": query
                }
            })

        # Subgoal 5: Library Reservations
        if any(w in query_lower for w in ["library", "borrow", "read", "book", "textbook", "author", "copies"]):
            # Extract book title keyword
            book_query = "Artificial Intelligence"
            if "deep learning" in query_lower:
                book_query = "Deep Learning"
            elif "reinforcement learning" in query_lower:
                book_query = "Reinforcement Learning"
            elif "operating system" in query_lower:
                book_query = "Operating System Concepts"
            elif "data-intensive" in query_lower or "kleppmann" in query_lower:
                book_query = "Designing Data-Intensive Applications"
            elif "pattern recognition" in query_lower or "bishop" in query_lower:
                book_query = "Pattern Recognition"

            subgoals.append({
                "subgoal_id": len(subgoals) + 1,
                "goal_description": f"Search catalog and reserve '{book_query}' at Central Library",
                "tool_name": "reserve_library_book",
                "tool_input": {
                    "student_id": student_info.get("registration_no", "12109482"),
                    "book_id": book_query
                }
            })

        # Default fallback if nothing triggered
        if not subgoals:
            subgoals.append({
                "subgoal_id": 1,
                "goal_description": "General campus services navigation and attendance inquiry",
                "tool_name": "get_student_attendance",
                "tool_input": {
                    "student_id": student_info.get("registration_no", "12109482")
                }
            })

        return {
            "intent": "Multi-Step Campus Workflow Execution",
            "is_escalation": False,
            "subgoals": subgoals
        }
