let currentDrafts = [];
let selectedDraftId = null;
let currentFilter = "all";

document.addEventListener("DOMContentLoaded", () => {
  initHealthCheck();
  loadAutonomyStatus();
  loadDrafts();
  loadAuditTrail();
  setupEventListeners();
});

function setupEventListeners() {
  // Search input
  document.getElementById("search-input").addEventListener("input", (e) => {
    renderEmailList(e.target.value.toLowerCase());
  });

  // Filter buttons
  document.querySelectorAll(".filter-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentFilter = btn.dataset.filter;
      renderEmailList();
    });
  });

  // Audit toggle
  document.getElementById("audit-toggle").addEventListener("click", () => {
    const wrapper = document.getElementById("audit-table-wrapper");
    wrapper.style.display = wrapper.style.display === "none" ? "block" : "none";
  });

  // Action Buttons
  document.getElementById("btn-approve").addEventListener("click", () => submitReview("approve"));
  document.getElementById("btn-edit-approve").addEventListener("click", () => submitReview("edit_and_approve"));
  document.getElementById("btn-reject").addEventListener("click", () => submitReview("reject"));
  document.getElementById("btn-escalate").addEventListener("click", () => submitReview("escalate"));
}

async function initHealthCheck() {
  try {
    const res = await fetch("/health");
    const data = await res.json();
    const statusEl = document.getElementById("service-status");
    statusEl.textContent = `Connected: ${data.knowledge_brain_url}`;
    statusEl.className = "status-pill status-connected";
  } catch (err) {
    const statusEl = document.getElementById("service-status");
    statusEl.textContent = "Offline / Local Mode";
    statusEl.className = "status-pill";
  }
}

async function loadAutonomyStatus() {
  try {
    const res = await fetch("/api/autonomy");
    const json = await res.json();
    renderAutonomyCards(json.autonomy);
  } catch (err) {
    console.error("Failed to load autonomy status:", err);
  }
}

function renderAutonomyCards(statuses) {
  const container = document.getElementById("autonomy-cards");
  container.innerHTML = "";

  statuses.forEach(st => {
    const card = document.createElement("div");
    card.className = `autonomy-card ${st.is_eligible ? "eligible" : ""}`;

    const percent = Math.min(100, Math.round((st.consecutive_approved_count / st.target_threshold) * 100));
    const title = st.category.replace(/_/g, " ");

    card.innerHTML = `
      <div class="autonomy-card-header">${title}</div>
      <div class="autonomy-streak">${st.consecutive_approved_count} / ${st.target_threshold}</div>
      <div class="autonomy-progress-bar">
        <div class="autonomy-progress-fill" style="width: ${percent}%;"></div>
      </div>
      <div class="autonomy-status-tag ${st.is_eligible ? 'text-eligible' : 'text-pending'}">
        ${st.is_eligible ? '&#10003; Eligible for Autonomy' : 'Human Review Required'}
      </div>
    `;
    container.appendChild(card);
  });
}

async function loadDrafts() {
  try {
    const res = await fetch("/api/drafts");
    const data = await res.json();
    currentDrafts = data.drafts;
    updateCounts();
    renderEmailList();

    if (currentDrafts.length > 0 && !selectedDraftId) {
      selectDraft(currentDrafts[0].id);
    }
  } catch (err) {
    console.error("Failed to load drafts:", err);
  }
}

function updateCounts() {
  const counts = {
    all: currentDrafts.length,
    pending_review: 0,
    approved: 0,
    edited: 0,
    rejected: 0,
    escalated: 0,
  };

  currentDrafts.forEach(d => {
    if (counts[d.status] !== undefined) {
      counts[d.status]++;
    }
  });

  document.getElementById("count-all").textContent = counts.all;
  document.getElementById("count-pending").textContent = counts.pending_review;
  document.getElementById("count-approved").textContent = counts.approved;
  document.getElementById("count-edited").textContent = counts.edited;
  document.getElementById("count-rejected").textContent = counts.rejected;
  document.getElementById("count-escalated").textContent = counts.escalated;
}

function renderEmailList(searchTerm = "") {
  const list = document.getElementById("email-list");
  list.innerHTML = "";

  const filtered = currentDrafts.filter(d => {
    const matchesFilter = currentFilter === "all" || d.status === currentFilter;
    const matchesSearch = !searchTerm ||
      d.sender.toLowerCase().includes(searchTerm) ||
      d.subject.toLowerCase().includes(searchTerm);
    return matchesFilter && matchesSearch;
  });

  if (filtered.length === 0) {
    list.innerHTML = `<div style="padding: 20px; text-align: center; color: #94a3b8; font-size: 0.85rem;">No emails match the filter.</div>`;
    return;
  }

  filtered.forEach(d => {
    const item = document.createElement("div");
    item.className = `email-item ${d.id === selectedDraftId ? 'selected' : ''}`;
    item.onclick = () => selectDraft(d.id);

    item.innerHTML = `
      <div class="item-top">
        <div class="item-sender">${escapeHtml(d.sender.split("<")[0].trim())}</div>
        <span class="badge badge-${d.priority}">${d.priority}</span>
      </div>
      <div class="item-subject">${escapeHtml(d.subject)}</div>
      <div class="item-tags">
        <span class="badge">${d.category.replace(/_/g, " ")}</span>
        <span class="badge badge-status-${d.status}">${d.status.replace(/_/g, " ")}</span>
      </div>
    `;
    list.appendChild(item);
  });
}

function selectDraft(draftId) {
  selectedDraftId = draftId;
  const draft = currentDrafts.find(d => d.id === draftId);
  if (!draft) return;

  renderEmailList();

  document.getElementById("empty-state").style.display = "none";
  document.getElementById("detail-content").style.display = "block";

  document.getElementById("view-subject").textContent = draft.subject;
  document.getElementById("view-sender").textContent = draft.sender;
  document.getElementById("view-time").textContent = new Date(draft.created_at).toLocaleString();

  const priorityEl = document.getElementById("view-priority");
  priorityEl.textContent = draft.priority;
  priorityEl.className = `badge badge-${draft.priority}`;

  const catEl = document.getElementById("view-category");
  catEl.textContent = draft.category.replace(/_/g, " ");

  const statusEl = document.getElementById("view-status");
  statusEl.textContent = draft.status.replace(/_/g, " ");
  statusEl.className = `badge badge-status-${draft.status}`;

  document.getElementById("view-body").textContent = draft.body;

  // Grounded Task 1 Evidence box
  const evidenceBox = document.getElementById("evidence-content");
  const providerBadge = document.getElementById("evidence-provider-badge");
  providerBadge.textContent = draft.is_mock ? "Mock Provider" : draft.provider;

  let evidenceHtml = "";
  if (draft.sources && draft.sources.length > 0) {
    evidenceHtml += `<strong>Grounded Sources:</strong>\n${draft.sources.map(s => `• ${s}`).join("\n")}\n\n`;
  }
  evidenceHtml += `<strong>Confidence Score:</strong> ${(draft.confidence * 100).toFixed(0)}%\n`;
  evidenceHtml += `<strong>Provenance:</strong> ${draft.disclaimer}\n`;

  if (draft.needs_escalation) {
    evidenceHtml += `\n⚠️ <strong>Flagged:</strong> Insufficient verified evidence found. Escalation suggested.`;
  }

  evidenceBox.textContent = evidenceHtml;

  // Reply Draft textarea
  const replyArea = document.getElementById("reply-textarea");
  replyArea.value = draft.final_reply || draft.suggested_reply;

  document.getElementById("reviewer-notes").value = draft.notes || "";
  if (draft.feedback_rating) {
    document.getElementById("feedback-rating").value = draft.feedback_rating;
  } else {
    document.getElementById("feedback-rating").value = "accurate_and_grounded";
  }
}

async function submitReview(action) {
  if (!selectedDraftId) return;

  const reviewerId = document.getElementById("reviewer-id").value.trim() || "Consultant Reviewer";
  const finalReply = document.getElementById("reply-textarea").value;
  const notes = document.getElementById("reviewer-notes").value.trim();
  const feedbackRating = document.getElementById("feedback-rating").value;

  try {
    const res = await fetch(`/api/drafts/${selectedDraftId}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action,
        reviewer_id: reviewerId,
        final_reply: finalReply,
        notes,
        feedback_rating: feedbackRating,
      }),
    });

    if (!res.ok) {
      const err = await res.json();

      alert(`Error submitting review: ${err.error || "Unknown error"}`);
      return;
    }

    const result = await res.json();

    // Refresh state
    await loadDrafts();
    await loadAutonomyStatus();
    await loadAuditTrail();

    // Select the draft again to reflect updated state
    selectDraft(selectedDraftId);
  } catch (err) {
    console.error("Failed to submit review:", err);
    alert("Network error submitting review.");
  }
}

async function loadAuditTrail() {
  try {
    const res = await fetch("/api/audit");
    const data = await res.json();
    document.getElementById("audit-count").textContent = data.count;

    const tbody = document.getElementById("audit-tbody");
    tbody.innerHTML = "";

    data.audit.forEach(entry => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${new Date(entry.timestamp).toLocaleTimeString()}</td>
        <td><code>${escapeHtml(entry.email_id)}</code></td>
        <td>${escapeHtml(entry.category.replace(/_/g, " "))}</td>
        <td>${escapeHtml(entry.reviewer_id)}</td>
        <td><span class="badge badge-status-${entry.action === 'approve' && !entry.diff_detected ? 'approved' : 'edited'}">${entry.action}</span></td>
        <td>${entry.diff_detected ? 'Yes (Reset)' : 'No (Qualified)'}</td>
        <td><strong>${entry.consecutive_approved_count} / 20</strong></td>
        <td>${entry.autonomy_eligible ? '<span class="text-eligible">Eligible</span>' : '<span class="text-pending">Guarded</span>'}</td>
        <td>${escapeHtml(entry.notes || "-")}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Failed to load audit trail:", err);
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
