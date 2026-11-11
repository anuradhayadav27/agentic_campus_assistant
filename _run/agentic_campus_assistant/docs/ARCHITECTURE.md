# SYSTEM ARCHITECTURE SPECIFICATION
## Agentic AI Assistant for Multi-Step Campus Workflows
**Course:** CSE276 Artificial Intelligence Foundations · Group 9 (Ruben Jose, Anupa Yadav, Erick Simon Kasole)

---

## 1. End-to-End ReAct Flowchart

```mermaid
flowchart TD
    User([Student User]) -->|Natural Language Query| API[FastAPI /api/chat]
    API --> Agent[CampusAgenticAI Engine]
    
    subgraph "1. Goal Decomposition & Planning"
        Agent --> Decomposer[Semantic Goal Decomposer]
        Decomposer --> Intent{Grievance / Sensitive?}
        Intent -->|Yes| EscalateTool[escalate_to_human_admin]
        Intent -->|No| Subgoals[Ordered Subgoal Queue: g1, g2, ..., gn]
    end

    subgraph "2. ReAct Execution & Tool Selection"
        Subgoals --> ToolSelector[Dynamic Tool Dispatcher]
        ToolSelector --> T1[Attendance Tool]
        ToolSelector --> T2[Lab Booking Tool]
        ToolSelector --> T3[Maintenance Tool]
        ToolSelector --> T4[Leave Tool]
        ToolSelector --> T5[Library Tool]
    end

    subgraph "3. Campus Relational Storage"
        T1 <--> DB[(Campus SQLite Database)]
        T2 <--> DB
        T3 <--> DB
        T4 <--> DB
        T5 <--> DB
    end

    subgraph "4. Observation & Dynamic Re-Planning Loop"
        T2 --> ObsCheck{Slot Status?}
        ObsCheck -->|Available| BookingSuccess[Seat Reserved]
        ObsCheck -->|FULL Conflict| RePlan[Dynamic Re-Planner]
        RePlan -->|Select Alternative Slot| T2
    end

    subgraph "5. Response Synthesis & Parallel Benchmark"
        BookingSuccess --> Synth[Response Synthesizer]
        EscalateTool --> Synth
        Agent --> BaselineSim[Rule-Based Chatbot Baseline Simulation]
        Synth --> FinalTrace[JSON ReAct Trace + Markdown Response]
    end

    FinalTrace --> UI[Modern Web Frontend Dashboard]
```

---

## 2. Sequence Diagram: Conflict Detection & Autonomous Re-Planning

```mermaid
sequenceDiagram
    autonumber
    actor Student as Student (Anupa Yadav)
    participant UI as Web Frontend
    participant Agent as CampusAgenticAI
    participant Decomposer as Goal Decomposer
    participant LabTool as lab_tools.py
    participant DB as SQLite DB

    Student->>UI: "Book Lab 34-601 tomorrow at 09:00 AM"
    UI->>Agent: POST /api/chat
    Agent->>Decomposer: plan_and_decompose()
    Decomposer-->>Agent: Subgoal: book_lab_slot(lab='LAB-34-601', time='09:00')
    
    Agent->>LabTool: book_lab_slot(LAB-34-601, 09:00 - 11:00)
    LabTool->>DB: Check slot capacity
    DB-->>LabTool: available_seats = 0 (STATUS: FULL)
    LabTool-->>Agent: {success: false, error_type: 'SLOT_FULL_CONFLICT', suggested_alternatives: ['11:00 - 13:00']}
    
    Note over Agent: RE-PLANNING TRIGGERED<br/>Intercepts failure state
    Agent->>LabTool: book_lab_slot(LAB-34-601, 11:00 - 13:00, "[Re-planned]")
    LabTool->>DB: Decrement seat count & record booking
    DB-->>LabTool: SUCCESS (Booking ID: LBK-8492)
    LabTool-->>Agent: {success: true, booking_id: 'LBK-8492'}
    
    Agent->>UI: Final Response + Trace with RE_PLANNED_SUCCESS badge
    UI-->>Student: Displays autonomous recovery confirmation
```

---

## 3. Database Entity-Relationship Architecture

```mermaid
erDiagram
    STUDENTS ||--o{ ATTENDANCE : has
    STUDENTS ||--o{ LAB_BOOKINGS : reserves
    STUDENTS ||--o{ MAINTENANCE_COMPLAINTS : logs
    STUDENTS ||--o{ LEAVE_APPLICATIONS : submits
    STUDENTS ||--o{ LIBRARY_RESERVATIONS : holds
    STUDENTS ||--o{ ESCALATION_TICKETS : creates

    LABS ||--o{ LAB_SLOTS : schedules
    LAB_SLOTS ||--o{ LAB_BOOKINGS : allocates
    LIBRARY_BOOKS ||--o{ LIBRARY_RESERVATIONS : reserves

    STUDENTS {
        string registration_no PK
        string name
        string section
        string program
        string email
        string hostel_block
        string room_no
    }

    ATTENDANCE {
        int id PK
        string student_id FK
        string course_code
        int classes_held
        int classes_attended
        float percentage
    }

    LAB_SLOTS {
        string slot_id PK
        string lab_id FK
        string date
        string time_range
        int available_seats
        string status
    }
```
