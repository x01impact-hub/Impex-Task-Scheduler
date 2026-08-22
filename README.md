# AI Assistant

A local AI-powered productivity assistant built with **Python, SQLite,
Ollama, and Qwen3 8B**.

The project combines natural-language task management with scheduling
and Windows desktop notifications. The backend is designed to keep task
data and model inference local to the user's machine.

## Highlights

-   Natural-language task commands
-   Task creation, viewing, updating, deletion, and filtering
-   Due dates, times, priorities, and task status
-   Local SQLite persistence
-   Local LLM inference through [Ollama](https://ollama.com/)
-   [Qwen3 8B](https://ollama.com/library/qwen3) for language
    understanding
-   Background task scheduling
-   Windows desktop notifications
-   Modular Python backend

## Techniques

### Structured AI actions

Natural-language input is converted into structured actions before the
backend performs database operations. This keeps model interpretation
separate from application logic and gives the backend a predictable
interface.

### Modular backend design

Responsibilities are separated by module:

-   [`Assistant.py`](./Assistant.py) --- command processing and
    assistant logic
-   [`ai.py`](./ai.py) --- communication with Ollama
-   [`database.py`](./database.py) --- SQLite operations
-   [`scheduler.py`](./scheduler.py) --- scheduled task processing
-   [`notifier.py`](./notifier.py) --- desktop notifications
-   [`config.py`](./config.py) --- application configuration
-   [`main.py`](./main.py) --- application entry point

### Local persistence

SQLite provides a lightweight embedded database without requiring a
separate database server.

### Background scheduling

The scheduler checks pending tasks independently of interactive command
processing, allowing reminders to be handled while the assistant remains
running.

## Technologies

  ---------------------------------------------------------------------------
  Technology                              Role
  --------------------------------------- -----------------------------------
  [Python](https://www.python.org/)       Application and backend logic

  [SQLite](https://www.sqlite.org/)       Local task persistence

  [Ollama](https://ollama.com/)           Local LLM runtime and API

  [Qwen3                                  Natural-language processing
  8B](https://ollama.com/library/qwen3)   

  [Git](https://git-scm.com/)             Version control

  [GitHub](https://github.com/)           Repository hosting
  ---------------------------------------------------------------------------

Ollama exposes a local API for application integration, and Qwen3 8B is
available directly through Ollama.

No custom fonts or frontend-specific libraries are documented in this
release because they are not part of the current backend project.

## Project Structure

``` text
AI_Assistant/
├── Assets/
│   └── Sound/
├── Exports/
├── ai.py
├── Assistant.py
├── config.py
├── database.py
├── main.py
├── notifier.py
├── scheduler.py
├── README.md
├── requirement.txt
└── .gitignore
```

### `Assets/`

Contains application assets, including notification sounds and the
project logo.

### `Exports/`

Contains generated export data and is kept outside version control.

## Architecture

``` text
                    User
                      |
                      v
                Assistant.py
                      |
          +-----------+-----------+
          |                       |
          v                       v
        ai.py                 database.py
          |                       |
          v                       v
       Ollama                  SQLite
      Qwen3 8B                   |
                                  v
                             scheduler.py
                                  |
                                  v
                            notifier.py
```

The AI layer interprets the request; the Python backend remains
responsible for executing task operations.

## Local Configuration

Local and generated data are intentionally excluded from Git:

``` text
.env
Assistant.db
.venv/
__pycache__/
Exports/
```

This keeps user-specific configuration, databases, virtual environments,
caches, and generated exports out of the repository.

## First Release Scope

The first release focuses on the local backend:

-   Task management
-   Natural-language commands
-   Local AI inference
-   SQLite storage
-   Scheduling
-   Windows desktop notifications

The next major stage is a frontend that communicates with the existing
backend.

## Development Direction

``` text
Core Backend
     |
     v
AI Integration
     |
     v
Scheduler + Notifications
     |
     v
Frontend
     |
     v
Frontend <-> Backend Integration
```

## License

No open-source license has been selected yet.