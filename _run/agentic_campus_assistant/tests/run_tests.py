import sys
import traceback
from agentic_campus_assistant.backend.database.db import init_db, reset_db
from agentic_campus_assistant.tests.test_agent import (
    test_attendance_tool,
    test_maintenance_complaint_tool,
    test_leave_application_policy_check,
    test_library_reservation_and_replanning_candidate,
    test_agent_multi_intent_goal_decomposition,
    test_agent_dynamic_replanning_on_conflict,
    test_agent_human_escalation,
    test_rule_based_comparison_difference,
    test_fastapi_endpoints
)

tests = [
    ("Database Reset & Initialization", reset_db),
    ("Attendance Tool & Threshold Verification", test_attendance_tool),
    ("Maintenance Complaint Tool & SLA", test_maintenance_complaint_tool),
    ("Leave Application Institutional Rules", test_leave_application_policy_check),
    ("Library Reservation & Re-Planning Prep", test_library_reservation_and_replanning_candidate),
    ("Agent Goal Decomposition (Multi-Intent)", test_agent_multi_intent_goal_decomposition),
    ("Agent Dynamic Re-Planning on Conflict", test_agent_dynamic_replanning_on_conflict),
    ("Agent Human Escalation Guardrails", test_agent_human_escalation),
    ("Rule-Based vs Agentic AI Baseline Divergence", test_rule_based_comparison_difference),
    ("FastAPI REST Endpoints & Web Integrity", test_fastapi_endpoints),
]

passed = 0
failed = 0

print("=" * 70)
print("RUNNING CSE276 AGENTIC AI TEST SUITE (GROUP 9: RUBEN, ANUPA, ERICK)")
print("=" * 70)

for name, func in tests:
    try:
        func()
        print(f" [PASS] {name}")
        passed += 1
    except Exception as e:
        print(f" [FAIL] {name}: {e}")
        traceback.print_exc()
        failed += 1

print("=" * 70)
print(f"RESULTS: {passed} PASSED, {failed} FAILED out of {len(tests)} tests.")
print("=" * 70)

if failed > 0:
    sys.exit(1)
else:
    print("ALL TESTS PASSED WITH 100% SUCCESS RATE!")
    sys.exit(0)
