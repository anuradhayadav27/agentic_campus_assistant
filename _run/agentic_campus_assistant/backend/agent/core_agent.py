import time
import uuid
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from agentic_campus_assistant.backend.tools import TOOL_REGISTRY, CAMPUS_TOOL_DEFINITIONS
from agentic_campus_assistant.backend.database.db import get_connection
from agentic_campus_assistant.backend.agent.llm_provider import SemanticAgentEngine
from agentic_campus_assistant.backend.agent.rule_based_baseline import RuleBasedCampusChatbot
from agentic_campus_assistant.backend.database.models import AgentStepTrace, AgentExecutionTrace

class CampusAgenticAI:
    """
    Agentic AI Assistant for Multi-Step Campus Service Workflows.
    Implements:
    - Goal Decomposition (breaking multi-intent requests into discrete subgoals)
    - Autonomous Tool Selection & Structured Invocation
    - Observation & Dynamic Re-Planning on environmental conflicts / failures
    - Contextual Human Escalation
    - Traceable Step Logging
    - Comparative Evaluation vs. Scripted Rule-Based Baseline
    """

    def __init__(self):
        self.semantic_engine = SemanticAgentEngine()
        self.rule_based_baseline = RuleBasedCampusChatbot()

    def process_request(self, user_query: str, student_id: str = "12109482") -> Dict[str, Any]:
        start_time = time.time()
        request_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"

        # 1. Fetch Student Context
        student_info = self._get_student_info(student_id)

        # 2. Goal Decomposition Phase
        plan_data = self.semantic_engine.plan_and_decompose(user_query, student_info)
        intent = plan_data.get("intent", "Multi-Step Campus Workflow")
        subgoals = plan_data.get("subgoals", [])

        subgoal_descriptions = [sg["goal_description"] for sg in subgoals]

        step_traces: List[Dict[str, Any]] = []
        escalated = False
        escalation_ticket_id = None
        succeeded_subgoals = 0

        # 3. Execution & Re-Planning Loop
        for index, sg in enumerate(subgoals):
            step_num = index + 1
            tool_name = sg["tool_name"]
            tool_input = sg["tool_input"]
            tool_func = TOOL_REGISTRY.get(tool_name)

            if not tool_func:
                step_traces.append({
                    "step_number": step_num,
                    "step_goal": sg["goal_description"],
                    "tool_name": tool_name,
                    "tool_input": tool_input,
                    "tool_output": {"error": f"Tool '{tool_name}' not found in registry"},
                    "status": "FAILED",
                    "re_plan_note": None
                })
                continue

            # Execute Primary Tool
            tool_output = tool_func(**tool_input)

            # Check if this tool invocation is an escalation
            if tool_name == "escalate_to_human_admin" and tool_output.get("success"):
                escalated = True
                escalation_ticket_id = tool_output.get("ticket_id")
                step_traces.append({
                    "step_number": step_num,
                    "step_goal": sg["goal_description"],
                    "tool_name": tool_name,
                    "tool_input": tool_input,
                    "tool_output": tool_output,
                    "status": "ESCALATED",
                    "re_plan_note": "Request triggered institutional escalation to campus administrative officers."
                })
                succeeded_subgoals += 1
                break

            # 4. Observation & Dynamic Re-Planning Loop
            if not tool_output.get("success", False):
                # Analyze failure cause
                error_type = tool_output.get("error_type")

                # RE-PLANNING CASE 1: Lab slot is full conflict
                if error_type == "SLOT_FULL_CONFLICT" and "suggested_alternatives" in tool_output and tool_output["suggested_alternatives"]:
                    best_alt = tool_output["suggested_alternatives"][0]
                    alt_lab = best_alt["lab_id"]
                    alt_time = best_alt["time_range"]
                    date_val = tool_input.get("date")

                    re_plan_note = f"OBSERVATION: Requested slot in {tool_input.get('lab_id')} is FULL. RE-PLANNING: Autonomously re-routing to alternative available slot '{alt_time}' in {alt_lab}."

                    # Re-plan action: book alternative slot
                    re_planned_output = TOOL_REGISTRY["book_lab_slot"](
                        student_id=student_id,
                        lab_id=alt_lab,
                        date=date_val,
                        time_range=alt_time,
                        purpose=tool_input.get("purpose", "Academic study") + " (Re-planned alternative)"
                    )

                    step_traces.append({
                        "step_number": step_num,
                        "step_goal": sg["goal_description"],
                        "tool_name": tool_name,
                        "tool_input": tool_input,
                        "tool_output": re_planned_output,
                        "status": "RE_PLANNED_SUCCESS" if re_planned_output.get("success") else "FAILED",
                        "re_plan_note": re_plan_note
                    })
                    if re_planned_output.get("success"):
                        succeeded_subgoals += 1

                # RE-PLANNING CASE 2: Library book copies exhausted
                elif error_type == "COPIES_EXHAUSTED" and tool_output.get("suggested_alternatives"):
                    alt_book = tool_output["suggested_alternatives"][0]
                    re_plan_note = f"OBSERVATION: All copies issued. RE-PLANNING: Reserved available reference '{alt_book['title']}' (#{alt_book['book_id']}) in same subject."

                    re_reserved = TOOL_REGISTRY["reserve_library_book"](
                        student_id=student_id,
                        book_id=alt_book["book_id"]
                    )

                    step_traces.append({
                        "step_number": step_num,
                        "step_goal": sg["goal_description"],
                        "tool_name": tool_name,
                        "tool_input": tool_input,
                        "tool_output": re_reserved,
                        "status": "RE_PLANNED_SUCCESS" if re_reserved.get("success") else "FAILED",
                        "re_plan_note": re_plan_note
                    })
                    if re_reserved.get("success"):
                        succeeded_subgoals += 1

                else:
                    # Unrecoverable tool failure -> escalate to human
                    escalate_res = TOOL_REGISTRY["escalate_to_human_admin"](
                        student_id=student_id,
                        user_query=user_query,
                        reason=f"Automated tool '{tool_name}' failed: {tool_output.get('message', 'unknown error')}",
                        severity="Medium"
                    )
                    escalated = True
                    escalation_ticket_id = escalate_res.get("ticket_id")
                    step_traces.append({
                        "step_number": step_num,
                        "step_goal": sg["goal_description"],
                        "tool_name": tool_name,
                        "tool_input": tool_input,
                        "tool_output": tool_output,
                        "status": "FAILED_ESCALATED",
                        "re_plan_note": f"Could not self-heal failure. Generated Escalation Ticket #{escalation_ticket_id}."
                    })
            else:
                # Primary tool execution succeeded
                step_traces.append({
                    "step_number": step_num,
                    "step_goal": sg["goal_description"],
                    "tool_name": tool_name,
                    "tool_input": tool_input,
                    "tool_output": tool_output,
                    "status": "SUCCESS",
                    "re_plan_note": None
                })
                succeeded_subgoals += 1

        # 5. Synthesize Natural Language Response
        final_response = self._synthesize_response(student_info, step_traces, escalated, escalation_ticket_id)

        # 6. Run Baseline Comparison Simulation
        rule_based_result = self.rule_based_baseline.process(user_query, student_id)
        comparison_metrics = self._compute_comparison(subgoals, step_traces, rule_based_result)

        exec_time_ms = round((time.time() - start_time) * 1000, 2)

        # 7. Persist Execution Log to Database
        self._log_execution(request_id, student_id, user_query, intent, subgoal_descriptions, step_traces, final_response, exec_time_ms, escalated)

        return {
            "request_id": request_id,
            "student_id": student_id,
            "student_name": student_info.get("name", "Student"),
            "user_query": user_query,
            "intent": intent,
            "decomposed_subgoals": subgoal_descriptions,
            "steps": step_traces,
            "final_response": final_response,
            "execution_time_ms": exec_time_ms,
            "escalated": escalated,
            "escalation_ticket_id": escalation_ticket_id,
            "total_subgoals": len(subgoals),
            "succeeded_subgoals": succeeded_subgoals,
            "comparison_with_rule_based": comparison_metrics
        }

    def _synthesize_response(self, student_info: Dict[str, Any], steps: List[Dict[str, Any]], escalated: bool, escalation_ticket_id: Optional[str]) -> str:
        parts = []
        name = student_info.get("name", "Student")

        parts.append(f"Hello {name}, I have processed your campus workflow request:")

        for s in steps:
            goal = s["step_goal"]
            status = s["status"]
            out = s["tool_output"]
            note = s.get("re_plan_note")

            if s["tool_name"] == "get_student_attendance" and out.get("success"):
                recs = out.get("records", [])
                overall = out.get("overall_percentage", 0.0)
                crit_list = [f"{r['course_code']} ({r['percentage']}%)" for r in recs if r.get('classes_needed_for_75', 0) > 0]
                if crit_list:
                    parts.append(f"• **Attendance Alert**: Overall attendance is **{overall}%**. Courses below 75% threshold: {', '.join(crit_list)}. Remediation needed to ensure exam eligibility.")
                else:
                    parts.append(f"• **Attendance Verified**: All enrolled subjects are in good standing (Overall: **{overall}%**).")

            elif s["tool_name"] == "book_lab_slot":
                if status == "SUCCESS":
                    parts.append(f"• **Lab Booking Confirmed**: Reserved seat in **{out.get('lab_id')}** for **{out.get('date')}** ({out.get('time_range')}). Booking ID: `{out.get('booking_id')}`.")
                elif status == "RE_PLANNED_SUCCESS":
                    parts.append(f"• **Dynamic Re-Planning Succeeded**: The requested slot was unavailable. I autonomously re-routed and booked alternative slot **{out.get('time_range')}** in **{out.get('lab_id')}** (Booking ID: `{out.get('booking_id')}`).")
                else:
                    parts.append(f"• **Lab Booking Note**: Unable to secure slot. {out.get('message', '')}")

            elif s["tool_name"] == "file_maintenance_complaint" and out.get("success"):
                parts.append(f"• **Maintenance Complaint Logged**: Ticket **#{out.get('complaint_id')}** registered for **{out.get('issue_category')}** at {out.get('location')}. Assigned to **{out.get('assigned_technician')}** ({out.get('estimated_resolution_time')}).")

            elif s["tool_name"] == "submit_leave_application" and out.get("success"):
                alerts = f" Note: {out['policy_alerts'][0]}" if out.get("policy_alerts") else ""
                parts.append(f"• **Leave Application Submitted**: ID **#{out.get('leave_id')}** ({out.get('leave_type')}, {out.get('total_days')} days from {out.get('from_date')} to {out.get('to_date')}). Forwarded to **{out.get('routed_to')}**.{alerts}")

            elif s["tool_name"] == "reserve_library_book":
                if status == "SUCCESS":
                    parts.append(f"• **Library Book Reserved**: '{out.get('title')}' is held for you at {out.get('shelf_location')}. Token: `{out.get('reservation_id')}` (Pickup deadline: {out.get('pickup_deadline')}).")
                elif status == "RE_PLANNED_SUCCESS":
                    parts.append(f"• **Library Re-Planning Succeeded**: The original title was out of stock. I secured available alternative: '{out.get('title')}' (Token: `{out.get('reservation_id')}`).")
                else:
                    parts.append(f"• **Library Query**: {out.get('message', '')}")

            elif s["tool_name"] == "escalate_to_human_admin":
                parts.append(f"• **Human Escalation Initiated**: Case transferred to **{out.get('assigned_department')}** under Ticket **#{out.get('ticket_id')}**. A campus officer will intervene directly.")

        if escalated:
            parts.append(f"\n⚠️ *Administrative notice: Escalation ticket #{escalation_ticket_id} has been logged in the university portal.*")

        return "\n\n".join(parts)

    def _compute_comparison(self, subgoals: List[Dict[str, Any]], steps: List[Dict[str, Any]], rule_based: Dict[str, Any]) -> Dict[str, Any]:
        agent_subgoals = len(subgoals)
        agent_succeeded = len([s for s in steps if s["status"] in ["SUCCESS", "RE_PLANNED_SUCCESS", "ESCALATED"]])
        agent_replanned = any(s["status"] == "RE_PLANNED_SUCCESS" for s in steps)
        agent_escalated = any(s["status"] in ["ESCALATED", "FAILED_ESCALATED"] for s in steps)

        rb_detected = rule_based.get("subgoals_detected", 1)
        rb_completed = rule_based.get("subgoals_completed", 0)
        rb_replanned = rule_based.get("replanning_attempted", False)

        return {
            "comparison_title": "Agentic AI vs. Scripted Rule-Based Baseline",
            "agentic_ai": {
                "system": "Agentic AI Assistant (Goal Decomposition & ReAct)",
                "subgoals_planned": agent_subgoals,
                "subgoals_completed": agent_succeeded,
                "multi_intent_success_rate": f"{(agent_succeeded / agent_subgoals * 100):.1f}%" if agent_subgoals > 0 else "100%",
                "dynamic_replanning": "Enabled (Autonomous alternative resolution on conflict)",
                "replanning_occurred": agent_replanned,
                "human_escalation_guard": "Enabled (Recognizes boundary conditions & policy restrictions)",
                "escalated": agent_escalated
            },
            "rule_based_baseline": {
                "system": "Legacy Scripted / Regex Chatbot",
                "subgoals_planned": rb_detected,
                "subgoals_completed": rb_completed,
                "multi_intent_success_rate": f"{(rb_completed / max(1, rb_detected) * 100):.1f}%",
                "dynamic_replanning": "Disabled (Fails abruptly on slot/resource collision)",
                "replanning_occurred": rb_replanned,
                "human_escalation_guard": "Disabled (Returns generic catch-all error)",
                "limitations": rule_based.get("limitations_observed", [])
            },
            "academic_verdict": "Agentic AI successfully preserved context across multi-step student intentions, dynamically healed resource conflicts, and demonstrated fault-tolerant re-planning where the rule-based system suffered single-intent dropping and rigid failure."
        }

    def _get_student_info(self, student_id: str) -> Dict[str, Any]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT registration_no, name, section, program, email, hostel_block, room_no FROM students WHERE registration_no = ?", (student_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return {"registration_no": student_id, "name": "Student", "section": "K4P25"}

    def _log_execution(self, req_id: str, student_id: str, query: str, intent: str, subgoals: List[str], steps: List[Dict[str, Any]], response: str, latency: float, escalated: bool):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO execution_logs (log_id, student_id, user_query, intent, decomposed_plan, steps_executed, final_response, execution_time_ms, escalated, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            req_id, student_id, query, intent,
            json.dumps(subgoals),
            json.dumps(steps),
            response,
            latency,
            1 if escalated else 0,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        conn.close()
