import json
import re

import requests
from datetime import datetime
from database import get_tasks
#import sys
#print(sys.executable)
#print(sys.version)
TODAY = datetime.now().strftime("%Y-%m-%d")

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3:8b"

SYSTEM_PROMPT = """
You are the AI controller for a local AI Assistant.
Today's date is """ + TODAY +""".
When a resolved date or resolved time is provided in the prompt, ALWAYS use it.
Never recalculate dates like "today", "tomorrow", or "next Monday" if they have already been resolved.
Never invent dates or times.

Always respond with valid JSON only.

Supported actions:
- add_task
- update_task
- delete_task
- search_tasks
- view_tasks
- statistics
- chat

Rules:

1. If the user wants to add a task, return:

{
    "action": "add_task",
    "task": {
        "title": "...",
        "description": "...",
        "date": "...",
        "time": "...",
        "priority": "..."
    }
}


2. If the user wants to search tasks:

{
    "action": "search_tasks",
    "query": "..."
}

3. If the user wants to view tasks:

{
    "action": "view_tasks",
    "filters":{"status": "pending | completed | expired | all"}
}

4. If the user is chatting:

{
    "action": "chat",
    "response": "..."
}
5. If the user wants to update a task:

Example:

User:
Move task 3 to tomorrow at 7 PM.

Return:

{
    "action":"update_task",
    "task_id":3,
    "updates":{
        "due_date":"YYYY-MM-DD",
        "due_time":"19:00"
    }
}
User:
Change task 5 priority to High.

↓

{
    "action":"update_task",
    "task_id":5,
    "updates":{"priority":"High"}
}
6.If the user wants to delete a task:

User:
Delete task 5.

Return:

{
    "action":"delete_task",
    "task_id":5
}
User:
Remove task 2.

Return:

{
    "action":"delete_task",
    "task_id":2
}

General JSON Rules:

- Always return valid JSON.
- Never omit required fields.
- Always follow the JSON schema exactly.
- If description is missing, return "".
- If date is missing, return null.
- If time is missing, return null.
- If priority is not mentioned, return "medium".
- Never invent missing information.

## must ##
Never output <think> blocks.
Thinking must remain internal.
Return ONLY the final JSON object.
Do not explain your reasoning.

Return ONLY JSON.
Do not use markdown.
Do not explain your answer.
"""

## CHAT FUNCTION ##
def chat(prompt):
    payload = {
        "model": MODEL_NAME,
        "system": SYSTEM_PROMPT,
        "prompt": prompt,
        "stream": False,
        "think": False,
        "options": {"num_ctx": 4096}
}
    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        response_text = result["response"].strip()
        ##print("\nRAW RESPONSE:")
        ##print(result["response"])
        response_text = result["response"]
        ## removing the thinking block ##
        response_text = re.sub(r"<think>.*?</think>\s*", "", response_text, flags=re.DOTALL)
        return response_text
    except Exception as e:
        return f"Error: {str(e)}"

## for task summarization ##
def summarize_tasks():
    tasks = get_tasks()
    pending = tasks

    if not pending:
        return "You have no pending tasks right now. Nice and clear!"

    task_lines = "\n".join(
        f"- {t[1]} (due: {t[3] if t[3] else 'no due date'}, recurrence: {t[6] if t[6] else 'none'})"
        for t in pending
    )

    prompt = f"""You are a helpful assistant. Summarize the following pending tasks into a short,
                friendly, natural-language briefing for the user. Organize the summary by urgency —
                mention what's due soonest first, then things further out, then anything with no due date.
                Group related or same-day tasks together if it makes sense. Keep it concise (a few sentences,
                not a list repeat).
                Tasks:{task_lines}"""

    response = chat(prompt)
    try:
        data = json.loads(response)
        return data.get("response", response)
    except json.JSONDecodeError:
        return "No summary available."

## for task suggestions ##
def suggest_tasks():
    tasks = get_tasks()

    if not tasks:
        return "You don't have any tasks yet, so I don't have enough history to suggest anything."

    task_lines = "\n".join(
    f"- {t[1]} (due: {t[3] if t[3] else 'no due date'}, "
    f"recurrence: {t[6] if t[6] else 'none'}, "
    f"status: pending)"
    for t in tasks
)

    prompt = f"""You are a helpful assistant that reviews someone's task history and suggests
                2-3 NEW tasks they might want to add. Base suggestions on patterns you notice — recurring
                habits, things that are often done together, or gaps (e.g. a recurring task that seems to be
                missing this cycle). Do not repeat tasks that already exist. Keep each suggestion short,
                one line, and explain briefly why you're suggesting it.
                Task history:{task_lines}"""
    response = chat(prompt)
    return response


## Letting the BANDS flow lol ##
if __name__ == "__main__":
    while True:
        prompt = input("You: ")
        if prompt.lower() == "exit":
            break
        reply = chat(prompt)
        print("\nAI:")
        print(reply)
        print()