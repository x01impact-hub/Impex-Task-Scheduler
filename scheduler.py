from datetime import datetime, timedelta
from notifier import send_notification
#import sqlite3
import time
from database import (get_tasks, mark_as_completed, mark_as_expired, reschedule_task, mark_reminder_sent)

## Starting the Scheduler ##
def start_scheduler():
    while True:
        tasks = get_tasks()
        current_datetime = datetime.now().replace(second=0, microsecond=0)

        for task in tasks:
            task_id = task[0]
            title = task[1]
            description = task[2]
            due_date = task[3]
            due_time = task[4]
            priority = task[5]
            recurrence = task[6]
            remind_before = task[7]
            reminder_sent = task[8] if len(task) > 8 else 0

            if due_date is None or due_time is None:
                print(f"Skipping task {task_id}: missing due date or time.")
                continue

            task_datetime = datetime.strptime(f"{due_date} {due_time}","%Y-%m-%d %H:%M")
            ## RECURRENCE reminder ##
            reminder_datetime = task_datetime - timedelta(minutes=remind_before)
            if(
                remind_before > 0
                and reminder_sent == 0
                and reminder_datetime <= current_datetime < reminder_datetime + timedelta(minutes=1)
            ):
                send_notification(
                    f"Upcoming:{title}",
                    description,
                    priority,
                    due_time,
                )
                mark_reminder_sent(task_id)
                print(f"15-minute reminder sent for:{title}")
                
            print("=" * 40)
            print("Due Date     :", due_date)
            print("Due Time     :", due_time)
            print("Task Time    :", task_datetime)
            print("Current Time :", current_datetime)
            print("=" * 40)

            ## Task is due now (within the current minute) ##
            if task_datetime <= current_datetime < task_datetime + timedelta(minutes=1):

                try:
                    send_notification(
                        title,
                        description,
                        None,
                        priority,
                    )
                    print(f"Reminder sent for: {title}")
                    if recurrence == "none":
                        mark_as_completed(task_id)
                    else:
                        reschedule_task(task_id)
                   ## mark_as_completed(task_id)

                except Exception as e:
                    print("Notification Error:", e)

            ## Task is overdue by more than 1 minute ##
            elif current_datetime >= task_datetime + timedelta(minutes=1):
                if recurrence == "none":
                    mark_as_expired(task_id)
                    print(f"Task '{title}' has expired.")
                else:
                    reschedule_task(task_id)
                    print(f"Recurring task '{title}' Rescheduled.")
        #print("Checking again in 60 seconds...\n") ## check in  if scheduler not working or not  ##
        time.sleep(60)

if __name__ == "__main__":
    start_scheduler()