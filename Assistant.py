import json
import ai
import database
import re
from datetime import datetime, timedelta

# DATE PARSER (final version 4.0)

def parse_date(user_input):
    parsed_data = {
        "original_text": user_input,
        "date": None,
        "time": None
    }
    text = user_input.lower()
    today = datetime.now()
    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6
    }

    ## For TODAY ##
    if "today" in text:
        parsed_data["date"] = datetime.now().strftime("%Y-%m-%d")

    ## For TOMORROW ##
    elif "tomorrow" in text:
        tomorrow = datetime.now() + timedelta(days=1)
        parsed_data["date"] = tomorrow.strftime("%Y-%m-%d")
    
    if "next" in text:
        for day_name, day_number in weekdays.items():
            if day_name in text:
                today_weekday = today.weekday()
                days_ahead = day_number - today_weekday
                if days_ahead <= 0:
                    days_ahead += 7
                target_date = today + timedelta(days=days_ahead)
                parsed_data["date"] = target_date.strftime("%Y-%m-%d")
                return parsed_data

    return parsed_data

## TIME PARSER ##

def parse_time(user_input):
    parsed_data = {
        "time": None
    }
    text = user_input.lower()

    ## For Noon ##
    if "noon" in text:
        parsed_data["time"] = "12:00"
        return parsed_data

    ## For Midnight ##
    if "midnight" in text:
        parsed_data["time"] = "00:00"
        return parsed_data

    ## For AM / PM Time ##
    match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', text)

    if match:
        hour = int(match.group(1))
        minute = match.group(2)
        period = match.group(3)

        if minute is None:
            minute = "00"
        if period == "pm" and hour != 12:
            hour += 12
        if period == "am" and hour == 12:
            hour = 0
        parsed_data["time"] = f"{hour:02}:{minute}"
        return parsed_data
    
    ## For 24-hour format ##
    match = re.search(r'\b([01]?\d|2[0-3]):([0-5]\d)\b', text)
    if match:
        hour = int(match.group(1))
        minute = match.group(2)
        parsed_data["time"] = f"{hour:02}:{minute}"
        return parsed_data
    return parsed_data


## PRIORITY PARSER ##

def parse_priority(user_input):

    parsed_data = {
        "priority": None
    }
    text = user_input.lower()

    if "high" in text:
        parsed_data["priority"] = "high"
    elif "medium" in text:
        parsed_data["priority"] = "medium"
    elif "low" in text:
        parsed_data["priority"] = "low"
    return parsed_data


## PEOPLE PARSER ##
## Didn't use the advanced parser ##
def parse_people(user_input):
    parsed_data = {
        "people": []
    }
    return parsed_data


## LOCATION PARSER ##
## Didn't use the advanced parser ##

def parse_location(user_input):
    parsed_data = {
        "location": None
    }
    return parsed_data

#######   PROMPT BUILDER   #######


def build_prompt(parsed):

    prompt = f"""
User Request:
{parsed["original_text"]}

Resolved Date:
{parsed["date"]}

Resolved Time:
{parsed["time"]}

Resolved Priority:
{parsed["priority"]}

Resolved People:
{parsed["people"]}

Resolved Location:
{parsed["location"]}

The resolved date and time have already been calculated.

If the resolved values are not None,
use them while generating JSON.

Do NOT calculate today's or tomorrow's date again.

Return ONLY valid JSON.
Do NOT use markdown.
"""

    return prompt

## COMMAND PROCESSOR  AND CHECKER##
def process_command(user_input):
    parsed = {
    **parse_date(user_input),
    **parse_time(user_input),
    **parse_priority(user_input),
    **parse_people(user_input),
    **parse_location(user_input)
}# ALL THE PRINT IS COMMENTED SO IT SHOWS ONLY THE RESPONSE AND NOT THE DEBUG INFORMATION #
    # remove comment to ch3eck if its working  or not  #

    #print("\nParsed Data ")
    #print(parsed)

    prompt = build_prompt(parsed)

    #print("\nPrompt Sent To AI")
    #print(prompt)

    response = ai.chat(prompt)

    #print("\nRaw AI Response")
    #print(response)

    try:
        data = json.loads(response)

    except json.JSONDecodeError:
        print("Invalid JSON received.")
        return

    action = data.get("action")

    ## For further chat ##
    if action == "chat":
        print("\nAI:", data["response"])


    ## Add Task using Model ##

    elif action == "add_task":
        task = data["task"]

        if parsed.get("date") is not None:
            task["date"] = parsed["date"]
        if parsed.get("time") is not None:
            task["time"] = parsed["time"]
        if parsed.get("priority") is not None:
            task["priority"] = parsed["priority"]
        if task.get("date") is None:
            task["date"] = input("Enter due date (YYYY-MM-DD): ")
        if task.get("time") is None:
            task["time"] = input("Enter due time (HH:MM): ")
        if task.get("priority") is None:
            task["priority"] = input("Enter priority (High/Medium/Low): ")

        database.add_task(
            title=task.get("title"),
            description=task.get("description"),
            due_date=task.get("date"),
            due_time=task.get("time"),
            priority=task.get("priority", "medium")
        )

        print("\nTask added successfully!")

    ## Search Task using Model ##
    elif action == "search_tasks":
        query = data.get("query")
        database.search_tasks(query)

    ## Update Task using Model ##
    elif action == "update_task":
        database.update_task(
            task_id=data["task_id"],
            **data["updates"]
        )
        print("\nTask updated successfully!")


    ## Delete Task Using Model ##
    elif action == "delete_task":
        database.delete_task(
            task_id=data["task_id"]
        )
        print("\nTask deleted successfully!")

    ## View Tasks using Model ##
    elif action == "view_tasks":
        filters = data.get("filters", {})
        status = filters.get("status", "all")
        database.view_tasks(status)
        print("Unknown action:", action)

## MAIN To Continue Conversation ##
if __name__ == "__main__":
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == "exit":
            break
        process_command(user_input)