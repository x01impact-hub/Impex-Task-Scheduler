#print("RUNNING UPDATED MAIN.PY")
from ai import suggest_tasks, summarize_tasks
import threading
import scheduler
import database
from database import get_task_statistics, export_tasks_to_csv

def print_tasks(tasks):
    if not tasks:
        print("No tasks found.")
        return
    for task in tasks:
        print(f"ID: {task[0]}, Title: {task[1]}, Description: {task[2]}, Due Date: {task[3]}, Status: {task[4]}, Recurring: {task[5]}, Pre-reminder: {task[6]}")

database.create_database()

scheduler_thread = threading.Thread(
   target=scheduler.start_scheduler,
   daemon=True
)
scheduler_thread.start()

while True:
    print("\n========== AI TASK MANAGER ==========")
    print("1. Add Task")
    print("2. View Pending Tasks")
    print("3. View Completed Tasks")
    print("4. View Expired Tasks")
    print("5. View All Tasks")
    print("6. Update Task")
    print("7. Search Task")
    print("8. Delete Task")
    print("9. View Task Summary")
    print("10. Suggest Tasks")
    print("11. View Task Statistics")
    print("12. Export Tasks")
    print("13. Exit")

    choice = input("Enter your choice: ")

    if choice == "1":
        database.add_task()

    elif choice == "2":
        print_tasks(database.view_tasks("pending"))

    elif choice == "3":
        print_tasks(database.view_tasks("completed"))

    elif choice == "4":
        print_tasks(database.view_tasks("expired"))

    elif choice == "5":
        print_tasks(database.view_tasks())

    elif choice == "6":
        database.update_task()

    elif choice == "7":
        print_tasks(database.search_tasks())

    elif choice == "8":
        database.delete_task()

    elif choice == "9":
        print("\n--- Task Summary ---")
        print(summarize_tasks())

    elif choice == "10":
        print("\n--- Suggested Tasks ---")
        print(suggest_tasks())

    elif choice == "11":
        stats = get_task_statistics()
        print("\n========== TASK STATISTICS ==========\n")
        print(f" Total Tasks      : {stats['total']}")
        print(f" Pending Tasks    : {stats['pending']}")
        print(f"Completed Tasks  : {stats['completed']}")
        print(f"Completion Rate  : {stats['completion_rate']}%")

        print()
        
        print(f"Today's Tasks   : {stats['today']}")
        print(f"Tomorrow's Tasks : {stats['tomorrow']}")
        print(f"Tasks Completed Today      : {stats['completed_today']}")
        print(f"Tasks Completed This Week  : {stats['completed_week']}")
        print(f"Tasks Completed This Month : {stats['completed_month']}")

        print()

        print(f"Recurring Tasks  : {stats['recurring']}")
        print(f"Pre-reminders    : {stats['pre_reminder']}")

        print("\n-------------------------------------\n")
        
    elif choice == "12":
        print("\n========== EXPORT TASKS ==========")
        export_tasks_to_csv()

    elif choice == "13":
        print("Goodbye!")
        break

    else:
        print("Invalid choice. Please try again.")