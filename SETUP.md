# Project setup and startup

## Requirements

- Python 3.11 or newer
- MongoDB 6.0 or newer
- PowerShell or another terminal

## Local configuration

The API reads these variables from the environment:

```text
MONGO_URI=mongodb://127.0.0.1:27017
MONGO_DB=attendance_assignment_dev
```

For local development, these values are stored in `.env`. The real environment takes priority over `.env`. The `.env` file is ignored by Git and must never be committed.

## Install and seed

```powershell
cd D:\dubey\HRoneAssignement\candidate_kit
\.venv\Scripts\python.exe -m pip install -r requirements.txt
\.venv\Scripts\python.exe sample_seed.py
```

The seed script replaces the two development collections with the supplied sample data. Use a dedicated development database because it deletes existing sample collections.

## Start the API

```powershell
\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000 --reload
```

Readiness check:

```text
http://127.0.0.1:8000/health
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

MongoDB indexes are created automatically during application startup.
