let allTasks = [];
let currentFilter = "pending";
let editingTaskId = null;

const taskListEl = document.getElementById("task-list");
const taskCountEl = document.getElementById("task-count");
const focusTitleEl = document.getElementById("focus-title");
const ringProgress = document.getElementById("ring-progress");
const ringPercent = document.getElementById("ring-percent");
const ringCaption = document.getElementById("ring-caption");
const upcomingList = document.getElementById("upcoming-list");

const RING_CIRCUMFERENCE = 326.7; // 2 * pi * r(52)

const FILTER_TITLES = {
  all: "All Tasks",
  pending: "Your Focus",
  completed: "Completed",
  expired: "Expired",
};

// ---------- Wait for the pywebview bridge ----------
function whenApiReady(callback) {
  if (window.pywebview && window.pywebview.api) {
    callback();
  } else {
    window.addEventListener("pywebviewready", callback);
  }
}

whenApiReady(() => {
  loadTasks();
  setupNav();
  setupModal();
  setupChat();
});

// ---------- Loading & rendering tasks ----------
async function loadTasks() {
  try {
    allTasks = await window.pywebview.api.get_tasks(currentFilter);
  } catch (e) {
    console.error("Failed to load tasks", e);
    allTasks = [];
  }
  renderTaskList();
  renderProgress();
  renderUpcoming();
}

function renderTaskList() {
  taskListEl.innerHTML = "";
  focusTitleEl.textContent = FILTER_TITLES[currentFilter] || "Tasks";
  taskCountEl.textContent = `${allTasks.length} task${allTasks.length === 1 ? "" : "s"}`;

  if (allTasks.length === 0) {
    taskListEl.innerHTML = `<p class="empty-hint">No tasks here yet.</p>`;
    return;
  }

  allTasks.forEach((task) => {
    const row = document.createElement("div");
    row.className = "task-row";

    const isDone = task.status === "completed";

    row.innerHTML = `
      <button class="task-checkbox ${isDone ? "done" : ""}" data-id="${task.id}"></button>
      <div class="task-main">
        <p class="task-title ${isDone ? "done" : ""}">${escapeHtml(task.title)}</p>
        <p class="task-meta">${formatMeta(task)}</p>
      </div>
      <span class="priority-pill ${task.priority}">${capitalize(task.priority)}</span>
      <div class="task-actions">
        <button data-action="edit" data-id="${task.id}">Edit</button>
        <button data-action="delete" data-id="${task.id}">Delete</button>
      </div>
    `;
    taskListEl.appendChild(row);
  });

  // Checkbox toggle
  taskListEl.querySelectorAll(".task-checkbox").forEach((btn) => {
    btn.addEventListener("click", () => toggleComplete(btn.dataset.id));
  });

  // Edit / Delete
  taskListEl.querySelectorAll('[data-action="edit"]').forEach((btn) => {
    btn.addEventListener("click", () => openEditModal(btn.dataset.id));
  });
  taskListEl.querySelectorAll('[data-action="delete"]').forEach((btn) => {
    btn.addEventListener("click", () => deleteTask(btn.dataset.id));
  });
}

function formatMeta(task) {
  const parts = [];
  if (task.due_date) parts.push(task.due_date);
  if (task.due_time) parts.push(task.due_time);
  return parts.length ? parts.join(" · ") : "No due date";
}

function capitalize(s) {
  if (!s) return "";
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

// ---------- Progress ring ----------
async function renderProgress() {
  try {
    const stats = await window.pywebview.api.get_stats();
    const total = stats.total || 0;
    const completed = stats.completed || 0;
    const pct = total > 0 ? Math.round((completed / total) * 100) : 0;

    ringPercent.textContent = `${pct}%`;
    ringCaption.textContent = `${completed} of ${total} tasks done`;
    ringProgress.style.strokeDashoffset = RING_CIRCUMFERENCE - (RING_CIRCUMFERENCE * pct) / 100;
  } catch (e) {
    console.error("Failed to load stats", e);
  }
}

// ---------- Upcoming panel ----------
async function renderUpcoming() {
  try {
    const upcoming = await window.pywebview.api.get_upcoming(5);
    upcomingList.innerHTML = "";

    if (!upcoming || upcoming.length === 0) {
      upcomingList.innerHTML = `<p class="empty-hint">Nothing scheduled soon.</p>`;
      return;
    }

    upcoming.forEach((task) => {
      const item = document.createElement("div");
      item.className = "upcoming-item";
      item.innerHTML = `
        <span class="upcoming-title">${escapeHtml(task.title)}</span>
        <span class="upcoming-time">${task.due_date || ""} ${task.due_time || ""}</span>
      `;
      upcomingList.appendChild(item);
    });
  } catch (e) {
    console.error("Failed to load upcoming", e);
  }
}

// ---------- Nav / filters ----------
function setupNav() {
  document.querySelectorAll(".nav-item[data-filter]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".nav-item[data-filter]").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentFilter = btn.dataset.filter;
      loadTasks();
    });
  });
}

// ---------- Task actions ----------
async function toggleComplete(taskId) {
  try {
    await window.pywebview.api.toggle_complete(taskId);
    loadTasks();
  } catch (e) {
    console.error("Failed to toggle task", e);
  }
}

async function deleteTask(taskId) {
  if (!confirm("Delete this task?")) return;
  try {
    await window.pywebview.api.delete_task(taskId);
    loadTasks();
  } catch (e) {
    console.error("Failed to delete task", e);
  }
}

// ---------- Modal (add / edit) ----------
function setupModal() {
  const backdrop = document.getElementById("modal-backdrop");
  const form = document.getElementById("task-form");
  const modalTitle = document.getElementById("modal-title");

  document.getElementById("open-add-task").addEventListener("click", () => {
    editingTaskId = null;
    modalTitle.textContent = "Add task";
    form.reset();
    document.getElementById("task-id").value = "";
    backdrop.classList.add("open");
  });

  document.getElementById("cancel-modal").addEventListener("click", () => {
    backdrop.classList.remove("open");
  });

  backdrop.addEventListener("click", (e) => {
    if (e.target === backdrop) backdrop.classList.remove("open");
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const payload = {
      title: document.getElementById("field-title").value.trim(),
      description: document.getElementById("field-description").value.trim(),
      due_date: document.getElementById("field-date").value || null,
      due_time: document.getElementById("field-time").value || null,
      priority: document.getElementById("field-priority").value,
    };

    try {
      if (editingTaskId) {
        await window.pywebview.api.update_task(editingTaskId, payload);
      } else {
        await window.pywebview.api.add_task(payload);
      }
      backdrop.classList.remove("open");
      loadTasks();
    } catch (err) {
      console.error("Failed to save task", err);
    }
  });
}

function openEditModal(taskId) {
  const task = allTasks.find((t) => String(t.id) === String(taskId));
  if (!task) return;

  editingTaskId = taskId;
  document.getElementById("modal-title").textContent = "Edit task";
  document.getElementById("task-id").value = task.id;
  document.getElementById("field-title").value = task.title || "";
  document.getElementById("field-description").value = task.description || "";
  document.getElementById("field-date").value = task.due_date || "";
  document.getElementById("field-time").value = task.due_time || "";
  document.getElementById("field-priority").value = task.priority || "medium";

  document.getElementById("modal-backdrop").classList.add("open");
}

// ---------- AI chat ----------
function setupChat() {
  const chatForm = document.getElementById("chat-form");
  const chatInput = document.getElementById("chat-input");
  const chatLog = document.getElementById("chat-log");

  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (!text) return;

    appendChatMessage(text, "user");
    chatInput.value = "";

    const thinkingEl = appendChatMessage("Thinking…", "ai");

    try {
      const reply = await window.pywebview.api.ai_command(text);
      thinkingEl.querySelector("p").textContent = reply || "Done.";
      loadTasks(); // in case the command changed something
    } catch (err) {
      thinkingEl.querySelector("p").textContent = "Something went wrong reaching the AI.";
      console.error(err);
    }
  });
}

function appendChatMessage(text, who) {
  const chatLog = document.getElementById("chat-log");
  const msg = document.createElement("div");
  msg.className = `chat-msg ${who}`;
  msg.innerHTML = who === "ai"
    ? `<span class="ai-dot"></span><p>${escapeHtml(text)}</p>`
    : `<p>${escapeHtml(text)}</p>`;
  chatLog.appendChild(msg);
  chatLog.scrollTop = chatLog.scrollHeight;
  return msg;
}
