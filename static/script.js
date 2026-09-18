let allTasks = [];
let allLists = [];
let currentFilter = "all";
let currentListId = null;
let editingTaskId = null;
let isSearching = false;
let searchQuery = "";

const taskListEl = document.getElementById("taskList");
const taskCountEl = document.getElementById("taskCount");
const focusTitleEl = document.getElementById("focusTitle");
const progressPctEl = document.getElementById("progressPct");
const progressCaptionEl = document.getElementById("progressCaption");
const progressRingEl = document.getElementById("progressRing");
const upcomingListEl = document.getElementById("upcomingList");
const listsGroupEl = document.getElementById("listsGroup");

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
    loadLists();
    loadTasks();
    setupNav();
    setupModal();
    setupAssistant();
    setupSearch();
    setupStats();
    setupAssistantPanel();
    setupRefresh();
    setupListModal();
  });
});

// ---------- Loading & rendering tasks ----------
async function loadTasks() {
  try {
    if (isSearching) {
      allTasks = await window.pywebview.api.search_tasks(searchQuery);
    } else if (currentListId !== null) {
      allTasks = await window.pywebview.api.get_tasks("all", currentListId);
    } else {
      allTasks = await window.pywebview.api.get_tasks(currentFilter);
    }
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

  if (isSearching) {
    focusTitleEl.textContent = `Search: "${searchQuery}"`;
  } else if (currentListId !== null) {
    const list = allLists.find((l) => String(l.id) === String(currentListId));
    focusTitleEl.textContent = list ? list.name : "List";
  } else {
    focusTitleEl.textContent = FILTER_TITLES[currentFilter] || "Tasks";
  }

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
  if (task.recurrence && task.recurrence !== "none") {
    const label = task.recurrence.charAt(0).toUpperCase() + task.recurrence.slice(1);
    parts.push(`🔁 ${label}`);
  }
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

// ---------- Nav / status filters ----------
function setupNav() {
  document.querySelectorAll(".nav-item[data-filter]").forEach((item) => {
    item.addEventListener("click", () => {
      document.querySelectorAll(".nav-item[data-filter]").forEach((el) => el.classList.remove("active"));
      item.classList.add("active");
      currentFilter = item.dataset.filter;
      currentListId = null;
      isSearching = false;
      searchQuery = "";
      const searchInput = document.getElementById("searchInput");
      if (searchInput) searchInput.value = "";
      document.querySelectorAll(".list-item").forEach((el) => el.classList.remove("active"));
      loadTasks();
    });
  });
}

// ---------- Lists ----------
async function loadLists() {
  try {
    allLists = await window.pywebview.api.get_lists();
  } catch (e) {
    console.error("Failed to load lists", e);
    allLists = [];
  }
  renderLists();
  renderListOptions();
}

function renderLists() {
  listsGroupEl.innerHTML = "";

  if (allLists.length === 0) {
    listsGroupEl.innerHTML = `<p class="empty-hint">No lists yet.</p>`;
    return;
  }

  allLists.forEach((list) => {
    const item = document.createElement("div");
    item.className = "list-item" + (String(currentListId) === String(list.id) ? " active" : "");
    item.dataset.listId = list.id;

    item.innerHTML = `
      <span class="list-item-name">${escapeHtml(list.name)}</span>
      <span class="list-item-right">
        <span class="list-item-count">${list.count}</span>
        <button class="list-delete-btn" title="Delete list">✕</button>
      </span>
    `;

    item.querySelector(".list-item-name").addEventListener("click", () => selectList(list.id));
    item.querySelector(".list-item-count").addEventListener("click", () => selectList(list.id));
    item.querySelector(".list-delete-btn").addEventListener("click", (e) => {
      e.stopPropagation();
      deleteList(list.id, list.name);
    });

    listsGroupEl.appendChild(item);
  });
}

function renderListOptions() {
  const select = document.getElementById("fieldList");
  if (!select) return;

  // Keep the first "No list" option, replace everything after it
  select.innerHTML = `<option value="0">No list</option>`;
  allLists.forEach((list) => {
    const opt = document.createElement("option");
    opt.value = list.id;
    opt.textContent = list.name;
    select.appendChild(opt);
  });
}

function selectList(listId) {
  currentListId = listId;
  isSearching = false;
  searchQuery = "";
  const searchInput = document.getElementById("searchInput");
  if (searchInput) searchInput.value = "";
  document.querySelectorAll(".nav-item[data-filter]").forEach((el) => el.classList.remove("active"));
  renderLists();
  loadTasks();
}

async function deleteList(listId, listName) {
  if (!confirm(`Delete "${listName}"? Tasks in it will not be deleted, just unassigned.`)) return;
  try {
    await window.pywebview.api.delete_list(listId);
    if (String(currentListId) === String(listId)) {
      currentListId = null;
      currentFilter = "all";
      document.querySelector('.nav-item[data-filter="all"]').classList.add("active");
    }
    await loadLists();
    loadTasks();
  } catch (e) {
    console.error("Failed to delete list", e);
  }
}

function setupListModal() {
  const backdrop = document.getElementById("listModalBackdrop");
  const form = document.getElementById("listForm");
  const newListBtn = document.getElementById("newListBtn");
  const cancelBtn = document.getElementById("cancelListModal");

  newListBtn.addEventListener("click", () => {
    document.getElementById("listModalTitle").textContent = "New list";
    document.getElementById("listFieldId").value = "";
    document.getElementById("listFieldName").value = "";
    backdrop.classList.add("open");
  });

  cancelBtn.addEventListener("click", () => {
    backdrop.classList.remove("open");
  });

  backdrop.addEventListener("click", (e) => {
    if (e.target === backdrop) backdrop.classList.remove("open");
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = document.getElementById("listFieldName").value.trim();
    if (!name) return;

    try {
      await window.pywebview.api.create_list(name);
      backdrop.classList.remove("open");
      await loadLists();
    } catch (err) {
      console.error("Failed to create list", err);
    }
  });
}

// ---------- Search ----------
function setupSearch() {
  const searchInput = document.getElementById("searchInput");
  const searchBtn = document.getElementById("searchBtn");
  if (!searchInput || !searchBtn) return;

  function runSearch() {
    const text = searchInput.value.trim();
    if (!text) {
      isSearching = false;
      searchQuery = "";
      loadTasks();
      return;
    }
    isSearching = true;
    searchQuery = text;
    currentListId = null;
    document.querySelectorAll(".nav-item[data-filter]").forEach((el) => el.classList.remove("active"));
    document.querySelectorAll(".list-item").forEach((el) => el.classList.remove("active"));
    loadTasks();
  }

  searchBtn.addEventListener("click", runSearch);
  searchInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") runSearch();
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
    loadLists(); // list counts may have changed
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
    document.getElementById("fieldList").value = currentListId !== null ? String(currentListId) : "0";
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
      recurrence: document.getElementById("fieldRecurrence").value,
      remind_before: document.getElementById("fieldReminder").checked ? 15 : 0,
      list_id: document.getElementById("fieldList").value,
    };

    try {
      if (editingTaskId) {
        await window.pywebview.api.update_task(editingTaskId, payload);
      } else {
        await window.pywebview.api.add_task(payload);
      }
      backdrop.classList.remove("open");
      loadTasks();
      loadLists(); // list counts may have changed
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
  document.getElementById("fieldRecurrence").value = task.recurrence || "none";
  document.getElementById("fieldReminder").checked = (task.remind_before || 0) > 0;
  document.getElementById("fieldList").value = task.list_id ? String(task.list_id) : "0";

  document.getElementById("modalBackdrop").classList.add("open");
}

// ---------- Compact AI chat (main card) ----------
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
      loadTasks();
    } catch (err) {
      messageEl.textContent = "Something went wrong reaching the AI.";
      console.error(err);
    }
  }
}

// ---------- Statistics modal ----------
function setupStats() {
  const backdrop = document.getElementById("statsBackdrop");
  const grid = document.getElementById("statsGrid");
  const viewBtn = document.getElementById("viewStatsBtn");
  const closeBtn = document.getElementById("closeStats");
  if (!backdrop || !grid || !viewBtn || !closeBtn) return;

  viewBtn.addEventListener("click", async () => {
    try {
      const s = await window.pywebview.api.get_stats();

      const items = [
        ["Total tasks", s.total],
        ["Completion rate", `${s.completion_rate}%`],
        ["Pending", s.pending],
        ["Completed", s.completed],
        ["Expired", s.expired],
        ["Recurring", s.recurring],
        ["Due today", s.today],
        ["Due tomorrow", s.tomorrow],
        ["Completed today", s.completed_today],
        ["Completed this week", s.completed_week],
        ["Completed this month", s.completed_month],
        ["High priority", s.high],
        ["Medium priority", s.medium],
        ["Low priority", s.low],
        ["With reminders", s.pre_reminder],
      ];

      grid.innerHTML = items.map(([label, value]) => `
        <div class="stat-item">
          <div class="stat-value">${value}</div>
          <div class="stat-label">${label}</div>
        </div>
      `).join("");

      backdrop.classList.add("open");
    } catch (e) {
      console.error("Failed to load statistics", e);
    }
  });

  closeBtn.addEventListener("click", () => {
    backdrop.classList.remove("open");
  });

  backdrop.addEventListener("click", (e) => {
    if (e.target === backdrop) backdrop.classList.remove("open");
  });
}

// ---------- Expanded Assistant Panel ----------
function setupAssistantPanel() {
  const expandBtn = document.getElementById("expandAssistantBtn");
  const collapseBtn = document.getElementById("collapseAssistantBtn");
  const backdrop = document.getElementById("assistantPanelBackdrop");
  const chatLog = document.getElementById("chatLogExpanded");
  const form = document.getElementById("assistantPanelForm");
  const input = document.getElementById("assistantPanelInput");
  const summaryBtn = document.getElementById("summaryBtn");
  const suggestBtn = document.getElementById("suggestBtn");

  const required = { expandBtn, collapseBtn, backdrop, chatLog, form, input, summaryBtn, suggestBtn };
  for (const [name, el] of Object.entries(required)) {
    if (!el) {
      console.warn(`setupAssistantPanel: missing element "${name}" — check index.html IDs.`);
      return;
    }
  }

  expandBtn.addEventListener("click", () => {
    backdrop.classList.add("open");
    if (chatLog.children.length === 0) {
      appendPanelMessage("Hi! Ask me anything, or tap Task Summary / Suggest Tasks below.", "ai");
    }
  });

  collapseBtn.addEventListener("click", () => {
    backdrop.classList.remove("open");
  });

  backdrop.addEventListener("click", (e) => {
    if (e.target === backdrop) backdrop.classList.remove("open");
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;

    appendPanelMessage(text, "user");
    input.value = "";
    const thinking = appendPanelMessage("Thinking…", "ai");

    try {
      const reply = await window.pywebview.api.ai_command(text);
      thinking.querySelector("p").textContent = reply || "Done.";
      loadTasks();
    } catch (err) {
      thinking.querySelector("p").textContent = "Something went wrong reaching the AI.";
      console.error(err);
    }
  });

  summaryBtn.addEventListener("click", async () => {
    const thinking = appendPanelMessage("Summarizing your tasks…", "ai");
    try {
      const summary = await window.pywebview.api.get_summary();
      thinking.querySelector("p").textContent = summary;
    } catch (err) {
      thinking.querySelector("p").textContent = "Couldn't generate a summary.";
      console.error(err);
    }
  });

  suggestBtn.addEventListener("click", async () => {
    const thinking = appendPanelMessage("Thinking of a few suggestions…", "ai");
    try {
      const suggestions = await window.pywebview.api.get_suggestions();
      thinking.querySelector("p").textContent = suggestions;
    } catch (err) {
      thinking.querySelector("p").textContent = "Couldn't generate suggestions.";
      console.error(err);
    }
  });
}

function appendPanelMessage(text, who) {
  const chatLog = document.getElementById("chatLogExpanded");
  const msg = document.createElement("div");
  msg.className = `assistant-msg ${who}`;
  msg.innerHTML = who === "ai"
    ? `<div class="ai-dot"></div><p>${escapeHtml(text)}</p>`
    : `<p>${escapeHtml(text)}</p>`;
  chatLog.appendChild(msg);
  chatLog.scrollTop = chatLog.scrollHeight;
  return msg;
}

// ---------- Refresh button ----------
function setupRefresh() {
  const btn = document.getElementById("refreshBtn");
  if (!btn) return;

  btn.addEventListener("click", () => {
    btn.classList.add("spinning");
    loadLists();
    loadTasks();
    setTimeout(() => btn.classList.remove("spinning"), 400);
  });
}

// Auto-refresh every 60 seconds to pick up changes made by the
// background scheduler (expired tasks, recurring task resets, etc.)
setInterval(() => {
  loadTasks();
}, 60000);
