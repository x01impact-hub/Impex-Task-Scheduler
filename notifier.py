from win11toast import toast
from playsound import playsound


def send_notification(title, description, due_time=None, priority=None):
    try:
        ## Notification Title ##
        if priority is not None and priority.lower() == "high":
            notification_title = "🚨 High Priority Task"
        elif priority is not None:
            notification_title = "⏳ Upcoming Task"
        else:
            notification_title = "📌 AI Task Manager"

        ## Notification Body ##
        notification_body = (
            f"📝 Task : {title}\n\n"
            f"📄 Description : {description}\n\n"
        )
        ## Show time in both notifications ##
        if due_time is not None:
            notification_body += f"⏰ Due Time : {due_time}\n\n"

        ## Show priority ONLY in upcoming reminder ##
        if priority is not None:
            notification_body += f"🔥 Priority : {priority}"

        ## Notification Sound ##
        if priority is not None and priority.lower() == "high":
            playsound(
                r"D:\AI assistant 2\Assets\Sound\high_priority.mp3", block=False)
        else:
            playsound(r"D:\AI assistant 2\Assets\Sound\Reminder.mp3", block=False)
        toast(
            notification_title,
            notification_body,
            icon=r"D:\AI assistant 2\Assets\logo.png"
        )
    except Exception as e:
        print(f"Notification Error: {e}")

## USed to test if the notifier work or not ##
#if __name__ == "__main__":
#
#    send_notification(
#        "Finish Assignment",
#        "Complete Module 5",
#        "09:30 PM",
#        "medium"
#    )