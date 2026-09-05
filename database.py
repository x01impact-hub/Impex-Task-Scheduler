import csv
import sqlite3
from datetime import datetime #, timedelta
from dateutil.relativedelta import relativedelta
import os

#print("Working Directory:", os.getcwd())
#print("Database Path:", os.path.abspath("Assistant.db"))


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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP             
    )
    """)
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
        reminder_sent=None
):
    

    conn = sqlite3.connect("Assistant.db")
    cursor = conn.cursor()

        # Manual mode
    if title is None:
        title = input("Enter a task: ")

    if description is None:
        description = input("Enter description: ")

    if due_date is None:
        due_date = input("Enter due date (YYYY-MM-DD): ")


  ##  task = input("Enter a task:")
   ## description = input("Enter description: ")

##################################################################33
  ##v  due_date = input("Enter due date (YYYY-MM-DD): ")(OLD CODE JUST FOR KEEPSAKE)
   #DATA VALIDATION STEP TO CHECK #
   
    try:
         due_date = datetime.strptime(due_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
            print("Invalid date format! Please use YYYY-MM-DD.")
            conn.close()
            return False
    
###################################################################### 
    if due_time is None:
        due_time = input("Enter due time (HH:MM): ").strip()
    try:
         due_time = datetime.strptime(due_time,"%H:%M").strftime("%H:%M")
    except ValueError:
         print("Invalid time format! please use HH:MM.")
         conn.close()
         return False

##    
    if priority is None:
        priority = input("Enter priority (High/Medium/Low): ")
    status = 'pending'
    if recurrence is None:
        recurrence = input("Enter recurrence (None/Daily/Weekly/Monthly): ").strip().lower()
    if recurrence == "":
        recurrence ="none"
    status = 'pending'  # Default status for new tasks
    if remind_before is None:
        answer = input("Do you want a 15-minute reminder before the task? (yes/no):").strip().lower()
        if answer == "yes":
            remind_before = 15
        else:
            remind_before = 0      
          
    cursor.execute(
        "INSERT INTO tasks (title, description, due_date, due_time, priority, status, recurrence, remind_before) VALUES (?,?,?,?,?,?,?,?)",
        (title,
          description,
            due_date,
              due_time,
                priority,
                  status,
                    recurrence,
                    remind_before
                    ))
    conn.commit()
    conn.close()
    return True

## View tasks function ##
def view_tasks(status=None):

    conn = sqlite3.connect("Assistant.db")
    cursor = conn.cursor()

    # Show all tasks if no status is given
    if status is None:
        cursor.execute("""
            SELECT * FROM tasks
            ORDER BY due_date, due_time
        """)
    else:
        cursor.execute("""
            SELECT * FROM tasks
            WHERE status = ?
            ORDER BY due_date, due_time
        """, (status,))

    tasks = cursor.fetchall()

#    if not tasks:
#        print("\nNo tasks found.")
#        conn.close()
#        return
#
#    print("\n" + "=" * 60)
#
#   if status is None:
#        print("ALL TASKS")
#    else:
#        print(f"{status.upper()} TASKS")
#
#    print("=" * 60)
#
#    for task in tasks:
#        print(f"ID          : {task[0]}")
#        print(f"Title       : {task[1]}")
#        print(f"Description : {task[2]}")
#        print(f"Due Date    : {task[3]}")
#        print(f"Due Time    : {task[4]}")
#        print(f"Priority    : {task[5]}")
#        print(f"Status      : {task[6]}")
#        print(f"Created At  : {task[7]}")
#        print("-" * 60)

    conn.close()
    return tasks

## Delete Task Function ##
def delete_task(task_id= None):    
    conn = sqlite3.connect("Assistant.db")
    cursor = conn.cursor()

    if task_id is None:
        view_tasks()
        task_id = input("Enter the task id:").strip()

    cursor.execute(
            "DELETE FROM tasks WHERE id = ?",
            (task_id,)
        )

    conn.commit()
    if cursor.rowcount > 0:
        print(f"Task deleted successfully!")
    else:
        print(f"No task found with ID {task_id}.")
    conn.close()

## Update Task Function ##
def update_task(task_id=None,title=None,description=None,due_date=None,due_time=None,priority=None):
    conn = sqlite3.connect("Assistant.db")
    cursor = conn.cursor()

    # Manual mode — only prompt if called without a task_id (from main.py menu)
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
    if due_time:
        try:
            due_time = datetime.strptime(due_time, "%H:%M").strftime("%H:%M")
        except ValueError:
            print("Invalid time format!")
            conn.close()
            return

    updates = []
    values = []
## Build the SET clause for the UPDATE statement ##
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
def search_tasks(keyword=None):
    if keyword is None:
        keyword = input("Enter title or keyword to search: ")

    conn = sqlite3.connect("Assistant.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM tasks
        WHERE title LIKE ?
        OR description LIKE ?
        ORDER BY due_date, due_time
    """, (f"%{keyword}%", f"%{keyword}%"))

    tasks = cursor.fetchall()

#    if not tasks:
 #       print("\nNo matching tasks found.")
#        conn.close()
#        return
#
#    print("\nMatching Tasks")
 #   print("=" * 60)
#
 #   for task in tasks:
 #       print(f"ID          : {task[0]}")
#        print(f"Title       : {task[1]}")
#        print(f"Description : {task[2]}")
#        print(f"Due Date    : {task[3]}")
#        print(f"Due Time    : {task[4]}")
#        print(f"Priority    : {task[5]}")
#        print(f"Status      : {task[6]}")
#        print(f"Created At  : {task[7]}")
#        print("-" * 60)
#
    conn.close()
    return tasks

## GET NEXT DUE DATE function ##
def get_next_due_date(due_date, recurrence):
    ## Docstring parameters ##
   ## """
   ## Calculate the next due date for a recurring task.
   ## """

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
def reschedule_task(task_id):  ##
    ## """Update the due date of a recuring task in the database."""
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
    ## To keep the recurrence even after task wasn't called for days ##
    due_date, due_time, recurrence = task
    if due_date is None or due_time is None:
        print(f"Task {task_id} has invalid date/time. Cannot reschedule.")
        conn.close()
        return

    current_datetime = datetime.now().replace(second=0, microsecond=0)
    while True:
        task_datetime = datetime.strptime(
            f"{due_date} {due_time}",
            "%Y-%m-%d %H:%M"
        )
        if task_datetime > current_datetime:
            break
        due_date = get_next_due_date(due_date, recurrence)

#**************************************************************************#
#    current_due_date, recurrence = task
#    next_due_date = get_next_due_date(current_due_date, recurrence)
#
#    if next_due_date is None:
#        print("Invalid recurrence type.")
#        conn.close()
#        return
#**************************************************************************#
    cursor.execute(
        "UPDATE tasks SET due_date = ?, reminder_sent = 0 WHERE id = ?",
        (due_date, task_id)
    )
    conn.commit()
    conn.close()

    print(f"Task {task_id} rescheduled to {due_date}.")

## TASK MANAGEMENT ##
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
    cursor.execute(""" UPDATE tasks SET reminder_sent = 1 WHERE id = ?""",(task_id,))
    conn.commit()
    conn.close()

## TASK STatistics ##
def get_task_statistics():
    conn = sqlite3.connect("Assistant.db")
    cursor = conn.cursor()
    statistics = {}

    ## Total Tasks ##
    cursor.execute("SELECT COUNT(*) FROM tasks")
    statistics["total"] = cursor.fetchone()[0]

    ## Pending Tasks##
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending'")
    statistics["pending"] = cursor.fetchone()[0]

    ## Completed Tasks ##
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'completed'")
    statistics["completed"] = cursor.fetchone()[0]

    ## Expired Tasks ##
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'expired'")
    statistics["expired"] = cursor.fetchone()[0]

    ## High Priority ##
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE priority = 'High'")
    statistics["high"] = cursor.fetchone()[0]

    ## Medium Priority ##
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE priority = 'Medium'")
    statistics["medium"] = cursor.fetchone()[0]

    ## Low Priority ##
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE priority = 'Low'")
    statistics["low"] = cursor.fetchone()[0]

    ## Recurring Tasks ##
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE recurrence != 'none'")
    statistics["recurring"] = cursor.fetchone()[0]

    ## Tasks with 15-minute Reminder ##
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE remind_before = 15")
    statistics["pre_reminder"] = cursor.fetchone()[0]

    ## COMPLETION RATE ##
    if statistics["total"] > 0:
        statistics["completion_rate"] = round((statistics["completed"] / statistics["total"]) * 100, 2)
    else:
        statistics["completion_rate"] = 0.0
    conn.close()

    ## todays tasks ##
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE due_date = ?", (datetime.now().strftime("%Y-%m-%d"),))
    statistics["today"] = cursor.fetchone()[0]

    ## tomorrow's tasks ##
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE due_date = ?", (datetime.now().replace(day=datetime.now().day + 1).strftime("%Y-%m-%d"),))
    statistics["tomorrow"] = cursor.fetchone()[0]

    ## Tasks Completed Today ##
    today = datetime.now().strftime("%Y-%m-%d")

    cursor.execute("""
    SELECT COUNT(*)
    FROM tasks
    WHERE status = 'completed'
    AND DATE(completed_at) = ?
    """, (today,))
    statistics["completed_today"] = cursor.fetchone()[0]
    
    
    ## Tasks Completed This Week ##
    cursor.execute("""
    SELECT COUNT(*)
    FROM tasks
    WHERE status = 'completed'
    AND DATE(completed_at) >= DATE('now', 'weekday 0', '-6 days')
    """)
    statistics["completed_week"] = cursor.fetchone()[0]
    
    
    ## Tasks Completed This Month ##
    cursor.execute("""
    SELECT COUNT(*)
    FROM tasks
    WHERE status = 'completed'
    AND strftime('%Y-%m', completed_at) = strftime('%Y-%m', 'now')
    """)
    statistics["completed_month"] = cursor.fetchone()[0]

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

### MARK AS PENDING ##
def mark_as_pending(task_id):
    conn = sqlite3.connect("Assistant.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE tasks SET status = 'pending', completed_at = NULL WHERE id = ?",
        (task_id,)
    )

    conn.commit()
    conn.close()