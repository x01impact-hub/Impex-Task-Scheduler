let allTasks = [];
let currentFilter = "all";
let editingTaskId = null;

const taskListEl = document.getElementById("taskList");
const taskCountEl = document.getElementById("taskCount");
const focusTitleEl = document.getElementById("focusTitle");
const progressPctEl = document.getElementById("progressPct");
const progressCaptionEl = document.getElementById("progressCaption");
const progressRingEl = document.getElementById("progressRing");
const upcomingListEl = document.getElementById("upcomingList");

const FILTER_TITLES = {
  all: "All Tasks",
  pending: "Your Focus",
  completed: "Completed",
  expired: "Expired",
};

function whenApiReady(callback) {
  if (window.pywebview && window.pywebview.api) {
    callback();
  } else {
    window.addEventListener("pywebviewready", callback);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  whenApiReady(() => {
    loadTasks();
    setupNav();
    setupModal();
    setupAssistant();
  });
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
    const isDone = task.status === "completed";
    const row = document.createElement("div");
    row.className = "task-row";

    row.innerHTML = `
      <button class="checkbox ${isDone ? "done" : ""}" data-id="${task.id}"></button>
      <div class="task-body">
        <div class="task-name ${isDone ? "strike" : ""}">${escapeHtml(task.title)}</div>
        <div class="task-meta">${formatMeta(task)}</div>
      </div>
      <div class="row-actions">
        <span class="badge ${task.priority}">${task.priority.toUpperCase()}</span>
        <button class="icon-btn" data-action="edit" data-id="${task.id}">Edit</button>
        <button class="icon-btn" data-action="delete" data-id="${task.id}">Delete</button>
      </div>
    `;
    taskListEl.appendChild(row);
  });

  taskListEl.querySelectorAll(".checkbox").forEach((btn) => {
    btn.addEventListener("click", () => toggleComplete(btn.dataset.id));
  });
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

    progressPctEl.textContent = `${pct}%`;
    progressCaptionEl.textContent = `${completed} of ${total} task${total === 1 ? "" : "s"} done`;
    progressRingEl.style.background =
      `conic-gradient(var(--sage) ${pct * 3.6}deg, rgba(243,245,241,0.10) ${pct * 3.6}deg)`;
  } catch (e) {
    console.error("Failed to load stats", e);
  }
}

// ---------- Upcoming ----------
async function renderUpcoming() {
  try {
    const upcoming = await window.pywebview.api.get_upcoming(5);
    upcomingListEl.innerHTML = "";

    if (!upcoming || upcoming.length === 0) {
      upcomingListEl.innerHTML = `<p class="empty-hint">Nothing scheduled soon.</p>`;
      return;
    }

    upcoming.forEach((task) => {
      const item = document.createElement("div");
      item.className = "upcoming-item";
      item.innerHTML = `
        <div class="upcoming-name">${escapeHtml(task.title)}</div>
        <div class="upcoming-time">${task.due_date || ""} ${task.due_time || ""}</div>
      `;
      upcomingListEl.appendChild(item);
    });
  } catch (e) {
    console.error("Failed to load upcoming", e);
  }
}

// ---------- Nav / filters ----------
function setupNav() {
  document.querySelectorAll(".nav-item[data-filter]").forEach((item) => {
    item.addEventListener("click", () => {
      document.querySelectorAll(".nav-item[data-filter]").forEach((el) => el.classList.remove("active"));
      item.classList.add("active");
      currentFilter = item.dataset.filter;
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
  const backdrop = document.getElementById("modalBackdrop");
  const form = document.getElementById("taskForm");
  const modalTitle = document.getElementById("modalTitle");

  document.getElementById("addTaskBtn").addEventListener("click", () => {
    editingTaskId = null;
    modalTitle.textContent = "Add task";
    form.reset();
    document.getElementById("fieldId").value = "";
    backdrop.classList.add("open");
  });

  document.getElementById("cancelModal").addEventListener("click", () => {
    backdrop.classList.remove("open");
  });

  backdrop.addEventListener("click", (e) => {
    if (e.target === backdrop) backdrop.classList.remove("open");
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const payload = {
      title: document.getElementById("fieldTitle").value.trim(),
      description: document.getElementById("fieldDescription").value.trim(),
      due_date: document.getElementById("fieldDate").value || null,
      due_time: document.getElementById("fieldTime").value || null,
      priority: document.getElementById("fieldPriority").value,
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
  document.getElementById("modalTitle").textContent = "Edit task";
  document.getElementById("fieldId").value = task.id;
  document.getElementById("fieldTitle").value = task.title || "";
  document.getElementById("fieldDescription").value = task.description || "";
  document.getElementById("fieldDate").value = task.due_date || "";
  document.getElementById("fieldTime").value = task.due_time || "";
  document.getElementById("fieldPriority").value = task.priority || "medium";

  document.getElementById("modalBackdrop").classList.add("open");
}

// ---------- AI Assistant ----------
function setupAssistant() {
  const send = document.getElementById("assistantSend");
  const input = document.getElementById("assistantInput");
  const messageEl = document.getElementById("assistantMessage");

  send.addEventListener("click", () => sendAssistantMessage());
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendAssistantMessage();
  });

  async function sendAssistantMessage() {
    const text = input.value.trim();
    if (!text) return;

    messageEl.textContent = "Thinking…";
    input.value = "";

    try {
      const reply = await window.pywebview.api.ai_command(text);
      messageEl.textContent = reply || "Done.";
      loadTasks(); // in case the command changed something
    } catch (err) {
      messageEl.textContent = "Something went wrong reaching the AI.";
      console.error(err);
    }
  }
}
