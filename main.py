from ai import suggest_tasks, summarize_tasks
import threading
import scheduler
import database
from database import get_task_statistics, export_tasks_to_csv

database.create_database()

scheduler_thread = threading.Thread(
   target=scheduler.start_scheduler,
   daemon=True
)
scheduler_thread.start()


def print_tasks(tasks):
    if not tasks:
        print("\nNo tasks found.")
        return
    for task in tasks:
        print(f"ID          : {task[0]}")
        print(f"Title       : {task[1]}")
        print(f"Description : {task[2]}")
        print(f"Due Date    : {task[3]}")
        print(f"Due Time    : {task[4]}")
        print(f"Priority    : {task[5]}")
        print(f"Status      : {task[6]}")
        print("-" * 60)


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
    print("13. Manage Lists")
    print("14. Exit")

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
        keyword = input("Enter title or keyword to search: ")
        print_tasks(database.search_tasks(keyword))

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
        print("\n========== LISTS ==========")
        lists = database.get_lists()
        if not lists:
            print("No lists yet.")
        else:
            for list_id, name, count in lists:
                print(f"{list_id}. {name} ({count} tasks)")
        print("\na. Add a new list")
        print("r. Rename a list")
        print("d. Delete a list")
        print("b. Back")
        sub_choice = input("Choice: ").strip().lower()
        if sub_choice == "a":
            name = input("New list name: ")
            database.create_list(name)
        elif sub_choice == "r":
            list_id = input("List ID to rename: ")
            name = input("New name: ")
            database.rename_list(list_id, name)
        elif sub_choice == "d":
            list_id = input("List ID to delete: ")
            database.delete_list(list_id)

    elif choice == "14":
        print("Goodbye!")
        break

    else:
        print("Invalid choice. Please try again.")
