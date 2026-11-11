import re
from typing import Dict, Any, List

class RuleBasedCampusChatbot:
    """
    Baseline Rule-Based / Scripted Chatbot for Academic Comparison.
    Uses regex pattern matching and rigid finite-state logic.

    Demonstrates standard failure modes of non-agentic legacy systems:
    1. Single-intent bottleneck: drops subsequent goals in compound requests.
    2. Zero goal decomposition capability.
    3. Brittle error handling: no dynamic re-planning on slot conflicts or unavailable resources.
    4. Inability to recognize when human escalation is required.
    """

    def __init__(self):
        self.rules = [
            (r"\b(attendance|present|bunk|classes)\b", self._handle_attendance),
            (r"\b(book|reserve|slot)\b.*\b(lab|laboratory)\b", self._handle_lab_booking),
            (r"\b(complaint|broken|repair|fan|light|projector|ac)\b", self._handle_complaint),
            (r"\b(leave|holiday|absent|sick)\b", self._handle_leave),
            (r"\b(book|library|issue|borrow)\b", self._handle_library),
        ]

    def process(self, query: str, student_id: str = "12109482") -> Dict[str, Any]:
        query_clean = query.strip()
        matched_rule = None
        handler = None

        # Rule matching (matches first matching regex only)
        for pattern, func in self.rules:
            if re.search(pattern, query_clean, re.IGNORECASE):
                matched_rule = pattern
                handler = func
                break

        if not handler:
            return {
                "system_type": "Rule-Based Scripted Engine",
                "handled_successfully": False,
                "multi_step_supported": False,
                "subgoals_detected": 1,
                "subgoals_completed": 0,
                "replanning_attempted": False,
                "error_recovery": "None - Static Fallback",
                "response": "I didn't understand your command. Please use keywords like 'attendance', 'book lab', 'complaint', 'leave', or 'library'.",
                "limitations_observed": [
                    "Query does not match any predefined regex pattern.",
                    "Unable to generalize or infer intent from conversational phrasing."
                ]
            }

        result = handler(query_clean, student_id)
        result["system_type"] = "Rule-Based Scripted Engine"

        # Check if user query actually contained compound requests that were dropped
        intents_in_query = 0
        if re.search(r"attendance", query_clean, re.IGNORECASE): intents_in_query += 1
        if re.search(r"lab", query_clean, re.IGNORECASE): intents_in_query += 1
        if re.search(r"complaint|projector|repair", query_clean, re.IGNORECASE): intents_in_query += 1
        if re.search(r"leave", query_clean, re.IGNORECASE): intents_in_query += 1
        if re.search(r"library|book", query_clean, re.IGNORECASE): intents_in_query += 1

        if intents_in_query > 1:
            result["multi_step_supported"] = False
            result["subgoals_detected"] = intents_in_query
            result["subgoals_completed"] = 1
            result["limitations_observed"].append(
                f"Multi-step bottleneck: detected {intents_in_query} distinct student intents, but rule-based engine could only execute the first matched rule and silently discarded the remaining {intents_in_query - 1} tasks."
            )

        return result

    def _handle_attendance(self, query: str, student_id: str) -> Dict[str, Any]:
        return {
            "handled_successfully": True,
            "rule_matched": "attendance_regex",
            "subgoals_detected": 1,
            "subgoals_completed": 1,
            "replanning_attempted": False,
            "error_recovery": "N/A",
            "response": f"[Rule-Based Output]: Found attendance command. Student #{student_id} record retrieved. Please visit UMS portal to view detailed attendance breakdown.",
            "limitations_observed": [
                "Returns static template without computing remediation classes or evaluating conditional follow-up actions."
            ]
        }

    def _handle_lab_booking(self, query: str, student_id: str) -> Dict[str, Any]:
        return {
            "handled_successfully": False,
            "rule_matched": "lab_booking_regex",
            "subgoals_detected": 1,
            "subgoals_completed": 0,
            "replanning_attempted": False,
            "error_recovery": "None - Slot booking failed without alternative search",
            "response": "[Rule-Based Output]: Attempted booking for requested slot. ERROR: Slot conflict or missing parameter syntax. Please open university lab portal manually.",
            "limitations_observed": [
                "Cannot extract unstructured date/time parameters accurately.",
                "Zero re-planning: when a slot is full, fails with error instead of negotiating alternative available slots."
            ]
        }

    def _handle_complaint(self, query: str, student_id: str) -> Dict[str, Any]:
        return {
            "handled_successfully": True,
            "rule_matched": "complaint_regex",
            "subgoals_detected": 1,
            "subgoals_completed": 1,
            "replanning_attempted": False,
            "error_recovery": "N/A",
            "response": "[Rule-Based Output]: Complaint recorded in queue. Generic ticket generated.",
            "limitations_observed": [
                "Lacks facility/block extraction and cannot auto-route to specialized engineering teams based on semantic description."
            ]
        }

    def _handle_leave(self, query: str, student_id: str) -> Dict[str, Any]:
        return {
            "handled_successfully": True,
            "rule_matched": "leave_regex",
            "subgoals_detected": 1,
            "subgoals_completed": 1,
            "replanning_attempted": False,
            "error_recovery": "N/A",
            "response": "[Rule-Based Output]: Leave form initiated. Please print leave slip from UMS and sign by proctor.",
            "limitations_observed": [
                "No institutional policy validation (e.g., medical leave certificate thresholds or duty leave rules)."
            ]
        }

    def _handle_library(self, query: str, student_id: str) -> Dict[str, Any]:
        return {
            "handled_successfully": False,
            "rule_matched": "library_regex",
            "subgoals_detected": 1,
            "subgoals_completed": 0,
            "replanning_attempted": False,
            "error_recovery": "None",
            "response": "[Rule-Based Output]: Library catalog query executed. If copy is unavailable, request aborted.",
            "limitations_observed": [
                "Cannot perform semantic book matching or recommend related available titles upon out-of-stock."
            ]
        }
