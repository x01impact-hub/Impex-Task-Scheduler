import csv
import sqlite3
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os


## create database function ##
def create_database():

    conn = sqlite3.connect("Assistant.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        due_date TEXT,
        due_time TEXT,
        priority TEXT,
        status TEXT DEFAULT 'pending',
        recurrence TEXT DEFAULT 'none',
        remind_before INTEGER DEFAULT 0,
        reminder_sent INTEGER DEFAULT 0,
        completed_at TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        list_id INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Migration: if tasks table already existed from before this feature,
    # add the list_id column without losing existing data.
    cursor.execute("PRAGMA table_info(tasks)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    if "list_id" not in existing_columns:
        cursor.execute("ALTER TABLE tasks ADD COLUMN list_id INTEGER")

    conn.commit()
    conn.close()

    print("Database Ready!")


## Add Task Function ##
def add_task(
        title=None,
        description=None,
        due_date=None,
        due_time=None,
        priority=None,
        recurrence=None,
        remind_before=None,
        reminder_sent=None,
        list_id=None
):
    conn = sqlite3.connect("Assistant.db")
    cursor = conn.cursor()

    if title is None:
        title = input("Enter a task: ")

    if description is None:
        description = input("Enter description: ")

    if due_date is None:
        due_date = input("Enter due date (YYYY-MM-DD): ")

    try:
        due_date = datetime.strptime(due_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        print("Invalid date format! Please use YYYY-MM-DD.")
        conn.close()
        return False

    if due_time is None:
        due_time = input("Enter due time (HH:MM): ").strip()
    try:
        due_time = datetime.strptime(due_time, "%H:%M").strftime("%H:%M")
    except ValueError:
        print("Invalid time format! please use HH:MM.")
        conn.close()
        return False

    if priority is None:
        priority = input("Enter priority (High/Medium/Low): ")

    if recurrence is None:
        recurrence = input("Enter recurrence (None/Daily/Weekly/Monthly): ").strip().lower()
    if recurrence == "":
        recurrence = "none"

    status = 'pending'

    if remind_before is None:
        answer = input("Do you want a 15-minute reminder before the task? (yes/no):").strip().lower()
        if answer == "yes":
            remind_before = 15
        else:
            remind_before = 0

    cursor.execute(
        "INSERT INTO tasks (title, description, due_date, due_time, priority, status, recurrence, remind_before, list_id) VALUES (?,?,?,?,?,?,?,?,?)",
        (title, description, due_date, due_time, priority, status, recurrence, remind_before, list_id)
    )
    conn.commit()
    conn.close()
    return True


## View tasks function ##
def view_tasks(status=None, list_id=None):
    conn = sqlite3.connect("Assistant.db")
    cursor = conn.cursor()

    query = "SELECT * FROM tasks WHERE 1=1"
    params = []

    if status is not None:
        query += " AND status = ?"
        params.append(status)

    if list_id is not None:
        query += " AND list_id = ?"
        params.append(list_id)

    query += " ORDER BY due_date, due_time"

    cursor.execute(query, params)
    tasks = cursor.fetchall()
    conn.close()
    return tasks


## Delete Task Function ##
def delete_task(task_id=None):
    conn = sqlite3.connect("Assistant.db")
    cursor = conn.cursor()

    if task_id is None:
        view_tasks()
        task_id = input("Enter the task id:").strip()

    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    conn.commit()
    if cursor.rowcount > 0:
        print(f"Task deleted successfully!")
    else:
        print(f"No task found with ID {task_id}.")
    conn.close()


## Update Task Function ##
def update_task(task_id=None, title=None, description=None, due_date=None, due_time=None,
                 priority=None, recurrence=None, remind_before=None, list_id=None):
    conn = sqlite3.connect("Assistant.db")
    cursor = conn.cursor()

    if task_id is None:
        view_tasks()
        task_id = input("Enter the task ID of the task you want to update: ").strip()
    if title is None:
        title = input("Enter new title (leave blank to keep current): ").strip()
    if description is None:
        description = input("Enter new description (leave blank to keep current): ").strip()
    if due_date is None:
        due_date = input("Enter new due date (leave blank to keep current): ").strip()
    if due_time is None:
        due_time = input("Enter new due time (leave blank to keep current): ").strip()
    if priority is None:
        priority = input("New priority (High/Medium/Low) (leave blank to keep current): ").strip()
    if recurrence is None:
        recurrence = input("New recurrence (none/daily/weekly/monthly) (leave blank to keep current): ").strip()
    if remind_before is None:
        answer = input("Change 15-minute reminder? (yes/no/blank to keep current): ").strip().lower()
        if answer == "yes":
            remind_before = 15
        elif answer == "no":
            remind_before = 0
        else:
            remind_before = None

    if due_time:
        try:
            due_time = datetime.strptime(due_time, "%H:%M").strftime("%H:%M")
        except ValueError:
            print("Invalid time format!")
            conn.close()
            return

    updates = []
    values = []

    if title:
        updates.append("title = ?")
        values.append(title)

    if description:
        updates.append("description = ?")
        values.append(description)

    if due_date:
        updates.append("due_date = ?")
        values.append(due_date)

    if due_time:
        updates.append("due_time = ?")
        values.append(due_time)

    if priority:
        updates.append("priority = ?")
        values.append(priority)

    if recurrence:
        updates.append("recurrence = ?")
        values.append(recurrence)

    if remind_before is not None:
        updates.append("remind_before = ?")
        values.append(remind_before)

    if list_id is not None:
        updates.append("list_id = ?")
        values.append(list_id if list_id != 0 else None)

    if not updates:
        print("No changes made.")
        conn.close()
        return

    values.append(task_id)

    query = f"""
        UPDATE tasks
        SET {", ".join(updates)}
        WHERE id = ?
    """
    cursor.execute(query, values)
    conn.commit()
    conn.close()
    print("Task updated successfully!")


## Search Tasks Function ##
def search_tasks(keyword=None, list_id=None):
    if keyword is None:
        keyword = input("Enter title or keyword to search: ")

    conn = sqlite3.connect("Assistant.db")
    cursor = conn.cursor()

    query = """
        SELECT * FROM tasks
        WHERE (title LIKE ? OR description LIKE ?)
    """
    params = [f"%{keyword}%", f"%{keyword}%"]

    if list_id is not None:
        query += " AND list_id = ?"
        params.append(list_id)

    query += " ORDER BY due_date, due_time"

    cursor.execute(query, params)
    tasks = cursor.fetchall()
    conn.close()
    return tasks


## GET NEXT DUE DATE function ##
def get_next_due_date(due_date, recurrence):
    due_date = datetime.strptime(due_date, "%Y-%m-%d")
    recurrence = recurrence.lower()

    if recurrence == "daily":
        next_due_date = due_date + relativedelta(days=1)
    elif recurrence == "weekly":
        next_due_date = due_date + relativedelta(weeks=1)
    elif recurrence == "monthly":
        next_due_date = due_date + relativedelta(months=1)
    else:
        return None

    return next_due_date.strftime("%Y-%m-%d")


## FOR TASK REScHEDULING ##
def reschedule_task(task_id):
    conn = sqlite3.connect("Assistant.db")
    cursor = conn.cursor()
    cursor.execute(
        """SELECT due_date, due_time, recurrence FROM tasks WHERE id = ?""",
        (task_id,)
    )
    task = cursor.fetchone()
    if task is None:
        print("Task not found.")
        conn.close()
        return

    due_date, due_time, recurrence = task
    if due_date is None or due_time is None:
        print(f"Task {task_id} has invalid date/time. Cannot reschedule.")
        conn.close()
        return

    current_datetime = datetime.now().replace(second=0, microsecond=0)
    while True:
        task_datetime = datetime.strptime(f"{due_date} {due_time}", "%Y-%m-%d %H:%M")
        if task_datetime > current_datetime:
            break
        due_date = get_next_due_date(due_date, recurrence)

    cursor.execute(
        "UPDATE tasks SET due_date = ?, reminder_sent = 0 WHERE id = ?",
        (due_date, task_id)
    )
    conn.commit()
    conn.close()

    print(f"Task {task_id} rescheduled to {due_date}.")


## TASK MANAGEMENT (used by scheduler.py) ##
def get_tasks():
    conn = sqlite3.connect("Assistant.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, description, due_date, due_time, priority, recurrence, remind_before, reminder_sent
        FROM tasks
        WHERE status = 'pending'
    """)

    tasks = cursor.fetchall()
    conn.close()
    return tasks


## To mark the task as Completed ##
def mark_as_completed(task_id):
    conn = sqlite3.connect("Assistant.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE tasks SET status = 'completed', completed_at = ? WHERE id = ?",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), task_id)
    )

    conn.commit()
    conn.close()


## To mark the task as Pending again (uncheck) ##
def mark_as_pending(task_id):
    conn = sqlite3.connect("Assistant.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tasks SET status = 'pending', completed_at = NULL WHERE id = ?",
        (task_id,)
    )
    conn.commit()
    conn.close()


## To mark the task as Expired ##
def mark_as_expired(task_id):
    conn = sqlite3.connect("Assistant.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE tasks SET status = 'expired', completed_at = ? WHERE id = ?",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), task_id)
    )

    conn.commit()
    conn.close()


## MARK reminder sent ##
def mark_reminder_sent(task_id):
    conn = sqlite3.connect("Assistant.db")
    cursor = conn.cursor()
    cursor.execute("""UPDATE tasks SET reminder_sent = 1 WHERE id = ?""", (task_id,))
    conn.commit()
    conn.close()


## TASK STATISTICS ##
def get_task_statistics():
    conn = sqlite3.connect("Assistant.db")
    cursor = conn.cursor()
    statistics = {}

    cursor.execute("SELECT COUNT(*) FROM tasks")
    statistics["total"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending'")
    statistics["pending"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'completed'")
    statistics["completed"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'expired'")
    statistics["expired"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE priority = 'High'")
    statistics["high"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE priority = 'Medium'")
    statistics["medium"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE priority = 'Low'")
    statistics["low"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE recurrence != 'none'")
    statistics["recurring"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE remind_before = 15")
    statistics["pre_reminder"] = cursor.fetchone()[0]

    if statistics["total"] > 0:
        statistics["completion_rate"] = round((statistics["completed"] / statistics["total"]) * 100, 2)
    else:
        statistics["completion_rate"] = 0.0

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE due_date = ?", (datetime.now().strftime("%Y-%m-%d"),))
    statistics["today"] = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM tasks WHERE due_date = ?",
        (datetime.now().replace(day=datetime.now().day + 1).strftime("%Y-%m-%d"),)
    )
    statistics["tomorrow"] = cursor.fetchone()[0]

    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
    SELECT COUNT(*)
    FROM tasks
    WHERE status = 'completed'
    AND DATE(completed_at) = ?
    """, (today,))
    statistics["completed_today"] = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COUNT(*)
    FROM tasks
    WHERE status = 'completed'
    AND DATE(completed_at) >= DATE('now', 'weekday 0', '-6 days')
    """)
    statistics["completed_week"] = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COUNT(*)
    FROM tasks
    WHERE status = 'completed'
    AND strftime('%Y-%m', completed_at) = strftime('%Y-%m', 'now')
    """)
    statistics["completed_month"] = cursor.fetchone()[0]

    conn.close()
    return statistics


## EXPORTING tasks for CSV ##
def export_tasks_to_csv():
    conn = sqlite3.connect("Assistant.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, description, due_date, due_time, priority, recurrence, remind_before, reminder_sent, status, completed_at
        FROM tasks
    """)

    tasks = cursor.fetchall()
    conn.close()

    os.makedirs("Exports", exist_ok=True)
    filename = datetime.now().strftime("Exports/Export_%Y-%m-%d_%H-%M-%S.csv")
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Title", "Description", "Due Date", "Due Time", "Priority", "Recurrence", "Remind Before", "Reminder Sent", "Status", "Completed At"])
        writer.writerows(tasks)
        print(f"Tasks exported successfully:{filename}")
        return filename


## ---------- LISTS (watchlists / custom categories) ---------- ##

def create_list(name):
    if not name or not name.strip():
        return None
    conn = sqlite3.connect("Assistant.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO lists (name) VALUES (?)", (name.strip(),))
        conn.commit()
        new_id = cursor.lastrowid
        return new_id
    except sqlite3.IntegrityError:
        # a list with this name already exists
        return None
    finally:
        conn.close()


def get_lists():
    conn = sqlite3.connect("Assistant.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT l.id, l.name, COUNT(t.id)
        FROM lists l
        LEFT JOIN tasks t ON t.list_id = l.id
        GROUP BY l.id, l.name
        ORDER BY l.name COLLATE NOCASE
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows


def rename_list(list_id, new_name):
    if not new_name or not new_name.strip():
        return False
    conn = sqlite3.connect("Assistant.db")
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE lists SET name = ? WHERE id = ?", (new_name.strip(), list_id))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def delete_list(list_id):
    """
    Deletes the list itself. Tasks that belonged to it are NOT deleted —
    they're just unassigned (list_id set back to NULL), so nothing
    disappears from your task history by accident.
    """
    conn = sqlite3.connect("Assistant.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET list_id = NULL WHERE list_id = ?", (list_id,))
    cursor.execute("DELETE FROM lists WHERE id = ?", (list_id,))
    conn.commit()
    conn.close()
    return True
