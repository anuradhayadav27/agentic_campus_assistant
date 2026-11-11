# CSE276: ARTIFICIAL INTELLIGENCE FOUNDATIONS
## INDIVIDUAL VIVA VOCE PREPARATION GUIDE
### Group 9: Ruben Jose · Anupa Yadav · Erick Simon Kasole

This guide contains the exact technical questions, definitions, flowcharts, and model answers required to score maximum marks (30/30) in your CSE276 course viva.

---

## 1. THE 60-SECOND OPENING PITCH (All Group Members Should Memorize)
> *"Good morning, sir/madam. Our project is an **Agentic AI Assistant for Multi-Step Campus Service Workflows**.*
> 
> *Traditional university chatbots are passive and rule-based—they can only answer one question at a time, drop compound requests, and crash when an error occurs.*
> 
> *Our project implements an **Agentic AI architecture using the ReAct (Reasoning + Acting) loop**. When a student gives an unconstrained, compound request in natural language, our system:*
> 1. *Decomposes the goal into discrete, ordered subtasks,*
> 2. *Autonomously selects and executes tools across campus departments (Labs, Maintenance, Attendance, Leaves, Library),*
> 3. *Continuously observes execution feedback and dynamically re-plans if a slot is full or a book is out of stock, and*
> 4. *Safely escalates sensitive grievances to human administrators.*
> 
> *In our benchmark evaluation across 6 campus edge cases, our Agentic AI achieved a **93.8% subgoal completion rate**, compared to just **36.4%** for scripted rule-based systems."*

---

## 2. HIGH-PROBABILITY VIVA QUESTIONS & MODEL ANSWERS

### Q1: What is the fundamental difference between an 'Agent' and a standard 'Chatbot'?
**Model Answer:**
- A **standard chatbot** is a simple input-output mapping function: $f(\text{query}) \to \text{text}$. It is passive, stateless, single-turn, and cannot take actions in the external world.
- An **Agentic AI** possesses *agency*: it is an autonomous system that observes its environment, formulates a sequence of internal subgoals, selects and invokes external software tools (via API/function calling), inspects the execution results (observations), and dynamically updates its plan until the overarching goal is satisfied.

---

### Q2: Explain the ReAct (Reasoning + Acting) framework you implemented.
**Model Answer:**
ReAct stands for **Reasoning and Acting**. In each iteration of our agent loop:
1. **Thought / Plan:** The agent analyzes the user's input and current state to determine what needs to be done next (Goal Decomposition).
2. **Action / Tool Call:** The agent generates structured parameters and calls an external tool (e.g., `book_lab_slot(lab_id='LAB-34-601', time='11:00')`).
3. **Observation:** The agent inspects the tool's return payload (e.g., `status: 'SUCCESS'` or `error_type: 'SLOT_FULL_CONFLICT'`).
4. **Re-Plan / Synthesis:** If the observation indicates failure, the agent triggers a compensatory action; if successful, it moves to the next subgoal or synthesizes the final response.

---

### Q3: How does Goal Decomposition work in your project?
**Model Answer:**
Students typically speak in compound sentences, such as: *"Check my attendance in CSE276, and if needed book Lab 34-601 tomorrow, and report the broken projector in Room 601."*
Our Semantic Planner parses this compound input into a directed execution plan of atomic subgoals:
- **Subgoal 1:** `get_student_attendance(student_id='12109482', course_code='CSE276')`
- **Subgoal 2:** `book_lab_slot(student_id='12109482', lab_id='LAB-34-601', date='tomorrow', time='11:00')`
- **Subgoal 3:** `file_maintenance_complaint(block='Block 34', room_no='Room 601', issue='Projector')`

Each subgoal is executed with dependency tracking. A rule-based system fails here because it only matches the first keyword and drops the rest.

---

### Q4: Give a concrete example of your 'Dynamic Re-Planning' mechanism.
**Model Answer:**
In our project's database, the `09:00 - 11:00` slot for `LAB-34-601` is marked as **FULL** (0 available seats).
- When a student asks: *"Book Lab 34-601 tomorrow at 9 AM"*, the tool execution returns `SLOT_FULL_CONFLICT` along with candidate alternative slots.
- Rather than throwing an unhandled exception or printing an error message, our agent's **Observation Loop** intercepts the conflict.
- The agent activates the **Dynamic Re-Planner**, picks the best available alternative (e.g., `11:00 - 13:00` in `LAB-34-601`), executes the reservation, and informs the student of the autonomous recovery.

---

### Q5: How did you implement Human Escalation, and why is it necessary?
**Model Answer:**
Autonomous systems must know their boundaries. We implemented an institutional guardrail layer that monitors for:
1. Sensitive disciplinary accusations (e.g. cheating, misconduct, ragging),
2. Formal academic grade appeals,
3. Unrecoverable repeated tool failures.

When triggered, the agent does not attempt to resolve the issue autonomously; instead, it executes `escalate_to_human_admin()`, generates an official tracking ticket (e.g., `#ESC-7701`), assigns it to the **Dean of Student Affairs** or **Grievance Cell**, and gives the student the campus administration hotline.

---

### Q6: How does the attendance remediation math work?
**Model Answer:**
LPU enforces a strict 75% attendance criterion for examination eligibility. If a student's attendance is below 75%, our system calculates the exact number of consecutive classes $x$ the student must attend to cross the threshold:
$$\frac{\text{Attended} + x}{\text{Held} + x} \ge 0.75 \implies x \ge \frac{0.75 \times \text{Held} - \text{Attended}}{0.25}$$
For example, for Anupa Yadav in CSE276: Held = 40, Attended = 28 (70.0%).
$$x \ge \frac{0.75 \times 40 - 28}{0.25} = \frac{30 - 28}{0.25} = \frac{2}{0.25} = 8 \text{ classes}.$$
The agent reports that 8 consecutive classes are required.

---

## 3. INDIVIDUAL MEMBER DEFENSE CHEATSHEET

### For Ruben Jose:
- **Your Specialty:** ReAct Loop Architecture, Prompt-to-Subgoal Decomposition, and Rule-Based Baseline Engine.
- **Expected Question:** *"Ruben, walk me through how your agent orchestrates execution when two tools need to be called in sequence."*
- **Your Answer:** *"I designed the ReAct orchestrator in `core_agent.py`. The input prompt is first passed to the Semantic Planner, which yields an array of subgoals. The orchestrator iterates through the subgoals, dynamically looks up the callable function from our `TOOL_REGISTRY`, unpacks the typed dictionary arguments, executes the call against SQLite, and stores the output in `step_traces`. If a step succeeds, state is updated and passed to the next step; if it fails, our re-planner is invoked."*

---

### For Anupa Yadav:
- **Your Specialty:** Dynamic Re-Planning Loop, Failure Interception, Lab Booking Tool, and 75% Attendance Remediation Engine.
- **Expected Question:** *"Anupa, how does the system know when to re-plan versus when to report an error?"*
- **Your Answer:** *"In our tool architecture, each tool returns a standardized JSON payload with a `success` boolean and an `error_type` code. For recoverable resource conflicts—like `SLOT_FULL_CONFLICT` in lab reservations or `COPIES_EXHAUSTED` in library loans—the tool provides a `suggested_alternatives` list. The Re-Planning loop in `core_agent.py` catches this specific error type, selects the nearest alternative, and re-invokes the booking tool autonomously. If the error is unrecoverable, it escalates to human staff."*

---

### For Erick Simon Kasole:
- **Your Specialty:** Human Escalation Guardrails, Campus Relational Database Schema, Maintenance Complaints, and Leave Policy Routing.
- **Expected Question:** *"Erick, explain how leave policy verification and maintenance ticket routing are handled."*
- **Your Answer:** *"I built the database schema in SQLite and the institutional business logic in `leave_tools.py` and `maintenance_tools.py`. For leaves, we calculate total days from ISO dates: if medical leave exceeds 2 days, we enforce a mandatory fitness prescription flag; duty leave is routed to the HOD. For maintenance, complaints are parsed into categories like Projector or HVAC and auto-dispatched to specific technician teams with an SLA resolution window."*

---

## 4. SYSTEM RUN COMMANDS (Keep Handy in Terminal)
- **Launch Server:** `./run.sh` or `python -m uvicorn agentic_campus_assistant.backend.main:app --port 8000 --reload`
- **Open Interface:** `http://localhost:8000`
- **Run Tests:** `PYTHONPATH=. .venv/bin/python agentic_campus_assistant/tests/run_tests.py`
- **Run Benchmark:** `PYTHONPATH=. .venv/bin/python agentic_campus_assistant/backend/evaluation/benchmark.py`
