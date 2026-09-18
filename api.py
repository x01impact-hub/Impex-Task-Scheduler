import json
from datetime import datetime

import database
import ai
import Assistant


class Api:
    """Exposed to the frontend as window.pywebview.api"""

    # ---------- Reading tasks ----------
    def get_tasks(self, status="pending", list_id=None):
        status_arg = None if status in (None, "all") else status
        rows = database.view_tasks(status_arg, list_id)
        return [self._row_to_dict(row) for row in (rows or [])]

    def search_tasks(self, query, list_id=None):
        rows = database.search_tasks(query, list_id)
        return [self._row_to_dict(row) for row in (rows or [])]

    def get_upcoming(self, limit=5):
        rows = database.view_tasks("pending") or []
        upcoming = [self._row_to_dict(row) for row in rows if row[3]]  # has a due_date
        return upcoming[:limit]

    def get_stats(self):
        return database.get_task_statistics()

    # ---------- Mutating tasks ----------
    def add_task(self, payload):
        list_id = self._parse_list_id(payload.get("list_id"))
        return database.add_task(
            title=payload.get("title") or "Untitled task",
            description=payload.get("description") or "",
            due_date=payload.get("due_date") or _today_str(),
            due_time=payload.get("due_time") or "09:00",
            priority=payload.get("priority") or "medium",
            recurrence=payload.get("recurrence") or "none",
            remind_before=int(payload.get("remind_before") or 0),
            list_id=list_id,
        )

    def update_task(self, task_id, payload):
        # 0 means "explicitly unassign from any list" — always pass a real
        # value (never None) so database.update_task always applies it.
        list_id = self._parse_list_id(payload.get("list_id"))
        if list_id is None:
            list_id = 0

        database.update_task(
            task_id=task_id,
            title=payload.get("title") or "",
            description=payload.get("description") or "",
            due_date=payload.get("due_date") or "",
            due_time=payload.get("due_time") or "",
            priority=payload.get("priority") or "",
            recurrence=payload.get("recurrence") or "",
            remind_before=int(payload.get("remind_before", 0)),
            list_id=list_id,
        )
        return True

    def delete_task(self, task_id):
        database.delete_task(task_id=task_id)
        return True

    def toggle_complete(self, task_id):
        rows = database.view_tasks(None) or []
        task = next((r for r in rows if str(r[0]) == str(task_id)), None)
        if task is None:
            return False

        status = task[6]
        if status == "completed":
            database.mark_as_pending(task_id)
        else:
            database.mark_as_completed(task_id)
        return True

    # ---------- Lists ----------
    def get_lists(self):
        rows = database.get_lists() or []
        return [{"id": r[0], "name": r[1], "count": r[2]} for r in rows]

    def create_list(self, name):
        new_id = database.create_list(name)
        return new_id

    def rename_list(self, list_id, name):
        return database.rename_list(list_id, name)

    def delete_list(self, list_id):
        return database.delete_list(list_id)

    # ---------- AI chat ----------
    def ai_command(self, text):
        return handle_ai_command(text)

    def get_summary(self):
        return ai.summarize_tasks()

    def get_suggestions(self):
        return ai.suggest_tasks()

    # ---------- helpers ----------
    def _parse_list_id(self, raw):
        if raw in (None, "", "0", 0):
            return None
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

    def _row_to_dict(self, row):
        # table order: id, title, description, due_date, due_time,
        # priority, status, recurrence, remind_before, reminder_sent,
        # completed_at, created_at, list_id
        return {
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "due_date": row[3],
            "due_time": row[4],
            "priority": (row[5] or "medium").lower(),
            "status": row[6],
            "recurrence": row[7] or "none",
            "remind_before": row[8] or 0,
            "list_id": row[12] if len(row) > 12 else None,
        }


def handle_ai_command(text):
    parsed = {
        **Assistant.parse_date(text),
        **Assistant.parse_time(text),
        **Assistant.parse_priority(text),
        **Assistant.parse_people(text),
        **Assistant.parse_location(text),
        **Assistant.parse_relative(text),
    }
    prompt = Assistant.build_prompt(parsed)
    response = ai.chat(prompt)

    try:
        data = json.loads(response)
    except json.JSONDecodeError:
        return "I couldn't quite understand that — try rephrasing."

    action = data.get("action")

    if action == "chat":
        return data.get("response", "...")

    if action == "add_task":
        task = data.get("task", {})
        date = parsed.get("date") or task.get("date") or _today_str()
        time_ = parsed.get("time") or task.get("time") or "09:00"
        priority = parsed.get("priority") or task.get("priority") or "medium"
        ok = database.add_task(
            title=task.get("title") or "Untitled task",
            description=task.get("description") or "",
            due_date=date,
            due_time=time_,
            priority=priority,
            recurrence="none",
            remind_before=0,
        )
        return "Task added." if ok else "Couldn't add that task — check the date/time format."

    if action == "search_tasks":
        query = data.get("query", "")
        results = database.search_tasks(query) or []
        if not results:
            return f'No tasks matching "{query}".'
        titles = ", ".join(r[1] for r in results[:5])
        return f"Found {len(results)} task(s): {titles}"

    if action == "view_tasks":
        status = data.get("filters", {}).get("status", "all")
        rows = database.view_tasks(None if status == "all" else status) or []
        return f"You have {len(rows)} {status} task(s)."

    if action == "update_task":
        updates = data.get("updates", {})
        database.update_task(
            task_id=data["task_id"],
            title=updates.get("title", ""),
            description=updates.get("description", ""),
            due_date=updates.get("due_date", ""),
            due_time=updates.get("due_time", ""),
            priority=updates.get("priority", ""),
        )
        return "Task updated."

    if action == "delete_task":
        database.delete_task(task_id=data["task_id"])
        return "Task deleted."

    return "Not sure how to handle that."


def _today_str():
    return datetime.now().strftime("%Y-%m-%d")
