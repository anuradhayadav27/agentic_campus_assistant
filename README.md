# Agentic AI Assistant for Multi-Step Campus Service Workflows
### Course Project: CSE276 — Artificial Intelligence Foundations (2026–27)
**Group 9 | Section K4P25 | Lovely Professional University**

---

## 👥 Group Members
| Name | Registration Number | Primary Responsibility |
|:---|:---:|:---|
| **Ruben Jose** | 12109483 | ReAct Architecture, Goal Decomposition, & Rule-Based Comparison |
| **Anupa Yadav** | 12109482 | Dynamic Re-Planning Loop, Failure Interception, & Attendance/Lab Tools |
| **Erick Simon Kasole** | 12109484 | Human Escalation Guardrails, Database Schema, & Maintenance/Leave/Library Tools |

---

## 📌 Project Overview
The **Agentic AI Campus Assistant** is an autonomous multi-step workflow engine designed to streamline university student operations across five functional campus departments:
1. **Lab Booking:** Real-time seat allocation with conflict detection and automated re-planning.
2. **Maintenance Complaints:** Infrastructure fault reporting with automatic technician team assignment and SLA tracking.
3. **Attendance Monitoring:** Subject-wise auditing with automated calculation of consecutive classes needed to cross the mandatory 75% threshold.
4. **Leave Applications:** Institutional workflow handling (Medical, Duty, Casual) with doctor prescription flags.
5. **Library Reservations:** Catalog search, 48-hour pickup token generation, and related-title recommendations on out-of-stock items.
6. **Human Escalation:** Safe routing of sensitive disciplinary grievances and academic appeals to university administrative officers.

---

## 🏆 Key Features Required by Course Rubric (30 Marks)
- ✅ **Goal Decomposition:** Splits compound requests into ordered subtasks (e.g., `"Check attendance AND book a lab"`).
- ✅ **Autonomous Tool Execution:** Structured function calling with typed parameters.
- ✅ **Observation & Dynamic Re-Planning:** Intercepts resource collisions (e.g. `SLOT_FULL_CONFLICT`) and autonomously books alternative slots without crashing.
- ✅ **Human Escalation Guardrails:** Generates official escalation tickets for administrative hearings and policy disputes.
- ✅ **Decision Logging & Traceability:** Full JSON trace of subgoals, tool parameters, observations, and latency.
- ✅ **Academic Benchmark vs. Scripted Chatbot:** Real-time evaluation against a regex/finite-state baseline demonstrating **93.8% vs. 36.4%** task completion.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.9+ (Python 3.12 recommended)
- Dependencies: `fastapi`, `uvicorn`, `pydantic` (already installed in the environment)

### 2. Single-Command Launch
```bash
./agentic_campus_assistant/run.sh
```

Or manually:
```bash
# 1. Run Tests
PYTHONPATH=. .venv/bin/python agentic_campus_assistant/tests/run_tests.py

# 2. Start Web Server
PYTHONPATH=. .venv/bin/python -m uvicorn agentic_campus_assistant.backend.main:app --port 8000 --reload
```

### 3. Open in Browser
Visit **`http://localhost:8000`** to access:
- **🤖 Interactive Assistant & ReAct Inspector:** Chat interface with live subtask and re-planning visualizer.
- **🏛️ Campus Services Hub:** Real-time database view of attendance, labs, bookings, complaints, leaves, and library holds.
- **📊 Benchmark Dashboard:** 1-click execution of the 6-scenario evaluation matrix.
- **📜 Decision Logs:** Complete JSON trace history.
- **🎓 Viva Voce & Architecture Guide:** Comprehensive Q&A sheet tailored for Ruben, Anupa, and Erick.

---

## 🧪 Running Automated Tests
```bash
PYTHONPATH=. .venv/bin/python agentic_campus_assistant/tests/run_tests.py
```
*Expected Output: 9 PASSED, 0 FAILED (100% Success Rate).*

---

## 📊 Running the Benchmark Suite
```bash
PYTHONPATH=. .venv/bin/python agentic_campus_assistant/backend/evaluation/benchmark.py
```

---

## 📁 Repository File Structure
```
agentic_campus_assistant/
├── backend/
│   ├── main.py                  # FastAPI server & static file mount
│   ├── agent/
│   │   ├── core_agent.py        # ReAct agent loop, decomposition, & re-planning
│   │   ├── llm_provider.py      # Semantic parser with zero-key offline support
│   │   └── rule_based_baseline.py # Scripted regex baseline for comparison
│   ├── database/
│   │   ├── db.py                # SQLite schema and realistic campus seed data
│   │   ├── models.py            # Pydantic data schemas & trace models
│   │   └── campus.db            # Persistent relational database
│   ├── tools/
│   │   ├── __init__.py          # Tool registry & function signatures
│   │   ├── attendance_tools.py  # 75% threshold & shortage calculator
│   │   ├── lab_tools.py         # Slot availability & conflict detection
│   │   ├── maintenance_tools.py # Facility fault reporting & technician dispatch
│   │   ├── leave_tools.py       # Leave policy validation & routing
│   │   ├── library_tools.py     # Catalog search & token reservation
│   │   └── escalation_tools.py  # Human administrative escalation
│   └── evaluation/
│       └── benchmark.py         # 6-scenario comparative test suite
├── frontend/
│   ├── index.html               # Responsive multi-tab dashboard
│   ├── style.css                # Dark tech-aesthetic glassmorphism styling
│   └── app.js                   # Client state, ReAct inspector, & API bindings
├── docs/
│   ├── PROJECT_REPORT.md        # Full academic report (LPU format)
│   ├── VIVA_PREPARATION_GUIDE.md# 15+ viva Q&As for Ruben, Anupa, & Erick
│   └── ARCHITECTURE.md          # Mermaid flowcharts & ER diagrams
├── tests/
│   ├── run_tests.py             # Complete test runner
│   └── test_agent.py            # Pytest test cases
├── run.sh                       # Single-command launcher script
└── README.md                    # Project documentation
```
