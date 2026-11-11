#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR/.."

echo "=========================================================="
echo " Starting Agentic AI Campus Assistant (Group 9)"
echo " Course: CSE276 Artificial Intelligence Foundations"
echo " Team: Ruben Jose · Anupa Yadav · Erick Simon Kasole"
echo "=========================================================="

# Check python environment
PYTHON_BIN=".venv/bin/python"
if [ ! -f "$PYTHON_BIN" ]; then
    PYTHON_BIN="python3"
fi

# 1. Run integrity tests
echo "[1/3] Running automated unit and integration tests..."
PYTHONPATH=. $PYTHON_BIN agentic_campus_assistant/tests/run_tests.py

# 2. Initialize database
echo "[2/3] Verifying and seeding campus relational database..."
PYTHONPATH=. $PYTHON_BIN agentic_campus_assistant/backend/database/db.py

# 3. Start server
echo "[3/3] Starting web server on http://localhost:8000 ..."
echo ">> Open your browser at: http://localhost:8000"
echo ">> Press Ctrl+C to stop the server."
PYTHONPATH=. $PYTHON_BIN -m uvicorn agentic_campus_assistant.backend.main:app --host 0.0.0.0 --port 8000
