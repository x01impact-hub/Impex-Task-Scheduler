import threading

import webview

import database
import scheduler
from api import Api


def start_background_scheduler():
    thread = threading.Thread(target=scheduler.start_scheduler, daemon=True)
    thread.start()


if __name__ == "__main__":
    database.create_database()
    start_background_scheduler()

    api = Api()
    webview.create_window(
        "AI Task Manager",
        "static/index.html",
        js_api=api,
        width=1280,
        height=800,
        min_size=(960, 640),
    )
    webview.start()
