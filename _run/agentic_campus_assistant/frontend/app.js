// State
let activeStudentId = "12109482";
const API_BASE = "";

// Tab Switching
function switchTab(tabId) {
  document.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("active"));
  document.querySelectorAll(".tab-content").forEach(content => content.classList.remove("active"));

  event.currentTarget.classList.add("active");
  const target = document.getElementById(tabId);
  if (target) target.classList.add("active");

  if (tabId === "tab-services") {
    loadCampusData();
  } else if (tabId === "tab-logs") {
    loadLogs();
  }
}

// Student Selection
function changeActiveStudent() {
  const select = document.getElementById("studentSelect");
  activeStudentId = select.value;
  console.log("Active student set to:", activeStudentId);
  loadCampusData();
}

// Quick Prompt Fill
function fillPrompt(text) {
  const input = document.getElementById("chatInput");
  input.value = text;
  input.focus();
}

function handleInputKey(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

// Clear Chat
function clearChat() {
  const container = document.getElementById("chatMessages");
  container.innerHTML = `
    <div class="message assistant-msg">
      <div class="msg-avatar">🤖</div>
      <div class="msg-body">
        <div class="msg-text">Chat history cleared. Ready for your campus requests!</div>
      </div>
    </div>
  `;
  document.getElementById("inspectorContent").innerHTML = `
    <div class="empty-state">
      <div class="empty-icon">🧠</div>
      <h4>No Active Execution Trace</h4>
      <p>Send a message in the chat to see real-time Goal Decomposition, Tool Execution, Dynamic Re-Planning, and Rule-Based Comparison!</p>
    </div>
  `;
  document.getElementById("inspectorStatus").innerText = "Awaiting Request";
  document.getElementById("inspectorStatus").className = "badge-tag";
}

// Send Chat Message
async function sendMessage() {
  const input = document.getElementById("chatInput");
  const sendBtn = document.getElementById("sendBtn");
  const query = input.value.trim();

  if (!query) return;

  // Append User Message
  appendUserMessage(query);
  input.value = "";
  sendBtn.disabled = true;
  sendBtn.innerText = "Processing...";

  document.getElementById("inspectorStatus").innerText = "ReAct Loop Running";
  document.getElementById("inspectorStatus").className = "badge-tag badge-orange";

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: query, student_id: activeStudentId })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Server error");
    }

    const data = await res.json();
    appendAssistantMessage(data.final_response, data.execution_time_ms);
    renderInspectorTrace(data);

    // Refresh services data in background
    loadCampusData();
  } catch (error) {
    appendAssistantMessage(`❌ **Error processing request**: ${error.message}`, 0);
  } finally {
    sendBtn.disabled = false;
    sendBtn.innerHTML = `<span>Send Request</span><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg>`;
  }
}

function appendUserMessage(text) {
  const container = document.getElementById("chatMessages");
  const div = document.createElement("div");
  div.className = "message user-msg";
  div.innerHTML = `
    <div class="msg-avatar">👤</div>
    <div class="msg-body">
      <div class="msg-text">${escapeHtml(text)}</div>
      <div class="msg-meta">Student ID: ${activeStudentId} · Just now</div>
    </div>
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function appendAssistantMessage(text, latencyMs) {
  const container = document.getElementById("chatMessages");
  const div = document.createElement("div");
  div.className = "message assistant-msg";

  // Simple Markdown parsing for bullet points & bold
  let formatted = escapeHtml(text)
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\n\n/g, "<br><br>")
    .replace(/• (.*?)<br>/g, "• $1<br>")
    .replace(/\n/g, "<br>");

  div.innerHTML = `
    <div class="msg-avatar">🤖</div>
    <div class="msg-body">
      <div class="msg-text">${formatted}</div>
      <div class="msg-meta">Agentic ReAct Pipeline · Executed in ${latencyMs}ms</div>
    </div>
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

// Render ReAct Inspector
function renderInspectorTrace(data) {
  const inspector = document.getElementById("inspectorContent");
  const statusBadge = document.getElementById("inspectorStatus");

  statusBadge.innerText = data.escalated ? "Escalated to Admin" : (data.steps.some(s => s.status === "RE_PLANNED_SUCCESS") ? "Re-Planned" : "Complete");
  statusBadge.className = "badge-tag " + (data.escalated ? "badge-red" : (data.steps.some(s => s.status === "RE_PLANNED_SUCCESS") ? "badge-orange" : "badge-green"));

  let subgoalsHtml = data.decomposed_subgoals.map((sg, i) => `
    <div class="subgoal-item">
      <span class="subgoal-badge">Subgoal ${i + 1}</span>
      <span>${escapeHtml(sg)}</span>
    </div>
  `).join("");

  let stepsHtml = data.steps.map(s => {
    let statusClass = "badge-green";
    if (s.status === "FAILED") statusClass = "badge-red";
    if (s.status === "RE_PLANNED_SUCCESS") statusClass = "badge-orange";
    if (s.status.includes("ESCALATED")) statusClass = "badge-red";

    let replanHtml = s.re_plan_note ? `
      <div class="replan-alert">
        <strong>🔄 Dynamic Re-Planning Triggered:</strong><br>${escapeHtml(s.re_plan_note)}
      </div>
    ` : "";

    return `
      <div class="step-card">
        <div class="step-card-header">
          <span class="tool-name-tag">🛠️ ${escapeHtml(s.tool_name)}()</span>
          <span class="badge-tag ${statusClass}">${escapeHtml(s.status)}</span>
        </div>
        <p style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.35rem;">${escapeHtml(s.step_goal)}</p>
        ${replanHtml}
      </div>
    `;
  }).join("");

  // Rule-based Comparison Box
  const comp = data.comparison_with_rule_based || {};
  const agenticComp = comp.agentic_ai || {};
  const ruleComp = comp.rule_based_baseline || {};

  inspector.innerHTML = `
    <!-- Intent & Request Info -->
    <div class="inspector-section">
      <div class="inspector-section-title">
        <span>Intent Identification</span>
        <span class="badge-tag badge-purple">${escapeHtml(data.intent)}</span>
      </div>
      <p style="font-size: 0.82rem; color: var(--text-muted);">
        Request ID: <code>${data.request_id}</code> | Execution Time: <strong>${data.execution_time_ms} ms</strong>
      </p>
    </div>

    <!-- Goal Decomposition -->
    <div class="inspector-section">
      <div class="inspector-section-title">
        <span>1. Goal Decomposition (${data.total_subgoals} Subgoals)</span>
        <span class="badge-tag badge-blue">Deterministic Planner</span>
      </div>
      <div class="subgoal-list">${subgoalsHtml}</div>
    </div>

    <!-- Step Execution & Re-Planning Trace -->
    <div class="inspector-section">
      <div class="inspector-section-title">
        <span>2. Tool Execution & Dynamic Re-Planning</span>
        <span class="badge-tag badge-green">${data.succeeded_subgoals}/${data.total_subgoals} Completed</span>
      </div>
      <div>${stepsHtml}</div>
    </div>

    <!-- Rule-Based Comparison -->
    <div class="comparison-box">
      <div class="inspector-section-title">
        <span>3. Comparative Baseline Divergence</span>
        <span class="badge-tag badge-orange">Academic Metric</span>
      </div>
      <div class="comparison-grid">
        <div class="comp-col" style="border-left: 3px solid var(--accent-blue);">
          <h5 style="color: var(--accent-blue);">Agentic AI Assistant</h5>
          <p>Subgoals: <strong>${agenticComp.subgoals_completed}/${agenticComp.subgoals_planned}</strong></p>
          <p>Re-Planning: <strong>${agenticComp.replanning_occurred ? "Yes (Self-Healed)" : "Not Required"}</strong></p>
          <p>Escalation: <strong>${agenticComp.escalated ? "Safe Hand-off" : "Not Required"}</strong></p>
        </div>
        <div class="comp-col" style="border-left: 3px solid var(--accent-amber);">
          <h5 style="color: var(--accent-amber);">Rule-Based Chatbot</h5>
          <p>Subgoals: <strong>${ruleComp.subgoals_completed}/${ruleComp.subgoals_planned}</strong></p>
          <p>Re-Planning: <strong>None (Crashes)</strong></p>
          <p>Escalation: <strong>None (Drops task)</strong></p>
        </div>
      </div>
      <p style="font-size: 0.78rem; color: var(--text-dim); margin-top: 0.6rem;">
        <em>${escapeHtml(comp.academic_verdict || "")}</em>
      </p>
    </div>
  `;
}

// Load Campus Services Data
async function loadCampusData() {
  try {
    const res = await fetch(`${API_BASE}/api/services/data?student_id=${activeStudentId}`);
    if (!res.ok) return;
    const data = await res.json();

    // 1. Attendance Table
    const attTbody = document.getElementById("attendanceTbody");
    const attBadge = document.getElementById("attOverallBadge");
    if (attTbody && data.selected_student_attendance) {
      let totalHeld = 0, totalAtt = 0;
      attTbody.innerHTML = data.selected_student_attendance.map(a => {
        totalHeld += a.classes_held;
        totalAtt += a.classes_attended;
        const pct = a.percentage;
        const isLow = pct < 75.0;
        return `
          <tr>
            <td><strong>${escapeHtml(a.course_code)}</strong></td>
            <td>${escapeHtml(a.course_name)}</td>
            <td>${a.classes_held}</td>
            <td>${a.classes_attended}</td>
            <td><strong>${pct}%</strong></td>
            <td><span class="badge-tag ${isLow ? 'badge-red' : 'badge-green'}">${isLow ? 'Below 75%' : 'Good'}</span></td>
          </tr>
        `;
      }).join("");

      const overall = totalHeld > 0 ? (totalAtt / totalHeld * 100).toFixed(1) : 0;
      attBadge.innerText = `Overall: ${overall}%`;
      attBadge.className = `badge-tag ${overall < 75 ? 'badge-red' : 'badge-green'}`;
    }

    // 2. Lab Slots Table
    const slotsTbody = document.getElementById("slotsTbody");
    if (slotsTbody && data.lab_slots) {
      slotsTbody.innerHTML = data.lab_slots.slice(0, 7).map(s => `
        <tr>
          <td><strong>${escapeHtml(s.lab_id)}</strong><br><small style="color:var(--text-dim)">${escapeHtml(s.lab_name)}</small></td>
          <td>${s.date}</td>
          <td>${s.time_range}</td>
          <td>${s.available_seats} seats</td>
          <td><span class="badge-tag ${s.status === 'AVAILABLE' ? 'badge-green' : 'badge-red'}">${s.status}</span></td>
        </tr>
      `).join("");
    }

    // 3. Recent Bookings Table
    const bookingsTbody = document.getElementById("bookingsTbody");
    if (bookingsTbody && data.recent_bookings) {
      bookingsTbody.innerHTML = data.recent_bookings.map(b => `
        <tr>
          <td><code>${b.booking_id}</code></td>
          <td>${escapeHtml(b.student_name)}</td>
          <td><strong>${escapeHtml(b.lab_id)}</strong></td>
          <td>${b.date} (${b.time_range})</td>
          <td><span class="badge-tag badge-green">${b.status}</span></td>
        </tr>
      `).join("");
    }

    // 4. Complaints Table
    const complaintsTbody = document.getElementById("complaintsTbody");
    if (complaintsTbody && data.complaints) {
      complaintsTbody.innerHTML = data.complaints.map(c => `
        <tr>
          <td><code>${c.complaint_id}</code></td>
          <td>${escapeHtml(c.block)}, ${escapeHtml(c.room_no)}</td>
          <td>${escapeHtml(c.issue_category)}</td>
          <td><span class="badge-tag ${c.priority === 'High' ? 'badge-red' : 'badge-orange'}">${c.priority}</span></td>
          <td>${escapeHtml(c.assigned_technician)}</td>
          <td><span class="badge-tag ${c.status === 'Resolved' ? 'badge-green' : 'badge-blue'}">${c.status}</span></td>
        </tr>
      `).join("");
    }

    // 5. Leave Applications Table
    const leavesTbody = document.getElementById("leavesTbody");
    if (leavesTbody && data.leave_applications) {
      leavesTbody.innerHTML = data.leave_applications.map(l => `
        <tr>
          <td><code>${l.leave_id}</code></td>
          <td><strong>${escapeHtml(l.leave_type)}</strong></td>
          <td>${l.from_date} to ${l.to_date}</td>
          <td>${l.total_days} days</td>
          <td>${escapeHtml(l.approval_authority)}</td>
          <td><span class="badge-tag ${l.status === 'Approved' ? 'badge-green' : 'badge-orange'}">${l.status}</span></td>
        </tr>
      `).join("");
    }

    // 6. Library Reservations
    const libTbody = document.getElementById("libraryTbody");
    if (libTbody && data.library_reservations) {
      libTbody.innerHTML = data.library_reservations.map(r => `
        <tr>
          <td><code>${r.reservation_id}</code></td>
          <td><strong>${escapeHtml(r.book_title)}</strong></td>
          <td>${escapeHtml(r.shelf_location)}</td>
          <td>${r.pickup_deadline}</td>
          <td><span class="badge-tag badge-green">Ready</span></td>
        </tr>
      `).join("");
    }

    // 7. Escalation Tickets
    const escTbody = document.getElementById("escalationsTbody");
    if (escTbody && data.escalation_tickets) {
      escTbody.innerHTML = data.escalation_tickets.map(e => `
        <tr>
          <td><code>${e.ticket_id}</code></td>
          <td>${escapeHtml(e.student_name)} (${e.student_id})</td>
          <td>${escapeHtml(e.reason)}</td>
          <td><span class="badge-tag badge-red">${e.severity}</span></td>
          <td>${escapeHtml(e.assigned_department)}</td>
          <td><span class="badge-tag badge-purple">${e.status}</span></td>
          <td>${e.created_at}</td>
        </tr>
      `).join("");
    }

  } catch (err) {
    console.error("Failed to load campus data:", err);
  }
}

// Run Benchmark
async function runBenchmark() {
  const tbody = document.getElementById("benchmarkTbody");
  tbody.innerHTML = `<tr><td colspan="6" class="text-center">Running 6 benchmark test cases through Agentic AI and Rule-Based baseline...</td></tr>`;

  try {
    const res = await fetch(`${API_BASE}/api/benchmark/run`);
    if (!res.ok) throw new Error("Benchmark failed");
    const report = await res.json();

    // Update Metrics
    const agg = report.aggregate_metrics;
    document.getElementById("agentSuccessRate").innerText = agg.agentic_ai.overall_subgoal_completion_rate;
    document.getElementById("ruleSuccessRate").innerText = agg.rule_based_baseline.overall_subgoal_completion_rate;
    document.getElementById("replanningEvents").innerText = `${agg.agentic_ai.dynamic_replanning_events} Events`;
    document.getElementById("escalationEvents").innerText = `${agg.agentic_ai.human_escalation_events} Escalations`;

    // Render Table
    tbody.innerHTML = report.detailed_results.map(r => `
      <tr>
        <td><code>${r.test_case_id}</code></td>
        <td><strong>${escapeHtml(r.test_case_name)}</strong><br><small style="color:var(--text-dim)">${escapeHtml(r.description)}</small></td>
        <td style="max-width: 250px; font-size: 0.8rem;"><em>"${escapeHtml(r.query)}"</em></td>
        <td>
          <span class="badge-tag badge-green">${r.agentic_ai.subgoals_completed}/${r.agentic_ai.subgoals_planned} Subgoals</span>
          ${r.agentic_ai.replanned ? '<span class="badge-tag badge-orange">Re-Planned</span>' : ''}
          ${r.agentic_ai.escalated ? '<span class="badge-tag badge-red">Escalated</span>' : ''}
          <br><small style="color:var(--text-muted)">${r.agentic_ai.latency_ms} ms</small>
        </td>
        <td>
          <span class="badge-tag ${r.rule_based_baseline.subgoals_completed < r.rule_based_baseline.subgoals_detected ? 'badge-red' : 'badge-green'}">
            ${r.rule_based_baseline.subgoals_completed}/${r.rule_based_baseline.subgoals_detected} Subgoals
          </span>
          <br><small style="color:var(--text-muted)">${r.rule_based_baseline.latency_ms} ms</small>
        </td>
        <td>
          <span class="badge-tag ${r.outcome.includes('Outperformed') ? 'badge-teal' : 'badge-blue'}">${r.outcome}</span>
        </td>
      </tr>
    `).join("");

  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center" style="color: var(--accent-red);">Error: ${err.message}</td></tr>`;
  }
}

// Load Logs
async function loadLogs() {
  const container = document.getElementById("logsContainer");
  container.innerHTML = `<div class="empty-state">Fetching logs...</div>`;

  try {
    const res = await fetch(`${API_BASE}/api/logs`);
    if (!res.ok) return;
    const data = await res.json();

    if (!data.logs || data.logs.length === 0) {
      container.innerHTML = `<div class="empty-state">No execution logs in database yet. Try running some queries in the AI Assistant tab!</div>`;
      return;
    }

    container.innerHTML = data.logs.map(log => `
      <div class="log-entry">
        <div class="log-entry-header">
          <div class="log-meta">Log ID: <code>${log.log_id}</code> · Student: <code>${log.student_id}</code> · ${log.created_at}</div>
          <div>
            <span class="badge-tag badge-purple">${escapeHtml(log.intent)}</span>
            <span class="badge-tag badge-blue">${log.execution_time_ms} ms</span>
            ${log.escalated ? '<span class="badge-tag badge-red">Escalated</span>' : ''}
          </div>
        </div>
        <div class="log-query">"${escapeHtml(log.user_query)}"</div>
        <div class="log-details">
          <pre>${escapeHtml(JSON.stringify(log.steps_executed, null, 2))}</pre>
        </div>
      </div>
    `).join("");

  } catch (err) {
    container.innerHTML = `<div class="empty-state" style="color:var(--accent-red)">Failed to load logs: ${err.message}</div>`;
  }
}

function escapeHtml(str) {
  if (typeof str !== "string") return String(str);
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

// Initial bootstrap
window.addEventListener("DOMContentLoaded", () => {
  loadCampusData();
});
