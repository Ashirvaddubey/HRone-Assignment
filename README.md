# Candidate kit

# Arifects
<img width="1427" height="835" alt="image" src="https://github.com/user-attachments/assets/6e6b1986-9da4-4c0b-b1a1-1d05fb41402a" />
<img width="1425" height="830" alt="image" src="https://github.com/user-attachments/assets/7d93aa92-0980-417c-8e43-3ca2fbd648cd" />
<img width="1350" height="719" alt="image" src="https://github.com/user-attachments/assets/6dbd2369-d90e-4251-b60e-ac24ccf0b613" />




Read in this order:

1. `PROBLEM_STATEMENT.docx`: what you are asked to do, how it is evaluated.
2. `openapi.yaml`: the API contract and the business rules (R1 - R10).
3. `DATA_MODEL.md`: what is stored in MongoDB, with nine sample documents.
4. `app/main.py`: the starter. Put **all** your code in this one file. It must start with `uvicorn app.main:app --port 8000`.
5. `REVIEW.md`, `DECISIONS.md`: review findings and implementation decisions.

`sample_data/` holds the nine sample documents as MongoDB Extended JSON; `sample_seed.py` loads them. The grader's dataset is
much larger and contains cases they do not show.

## Local setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # set MONGO_URI / MONGO_DB (local docker: docker run -p 27017:27017 mongo:7)
python sample_seed.py
uvicorn app.main:app --port 8000 --reload
```
MongoDB **6.0 or newer** is required (the grader uses 7.0). MongoDB Atlas free tier (M0) works.

On Windows, use `\.venv\Scripts\python.exe` to run the commands if PowerShell activation is restricted. The completed API includes the CRUD, punch-out, regularization, analytics, and explain routes. A focused local check is available at `tests/check_starter.py`.

## What is implemented

- FastAPI readiness check with MongoDB connectivity validation.
- Employee creation and filtered, sorted pagination.
- Attendance punch-in with strict epoch-millisecond validation, IST date rules, overnight shifts, late-minute calculation, and race-safe uniqueness.
- Attendance listing with employee, date, and status filters backed by MongoDB indexes.
- Punch-out with atomic closing, half-day calculation, work-hour half-up rounding, and overtime rules.
- Attendance regularization with validation, derived-field recomputation, and append-only audit history.
- Employee monthly summaries, department summaries, late leaderboard ranking, and department trend reporting.
- Explain output for the supported query and aggregation operations.

## Verification completed

The implementation was checked with the supplied sample data and focused edge-case tests for invalid input, pagination, IST boundaries, overnight shifts, rounding, duplicate concurrent requests, nested history timestamps, MongoDB availability, and index usage. MongoDB Compass explain plans confirmed `IXSCAN` for the employee/date attendance query and the monthly employee query.

The supporting documents explain the work in more detail:

- `SETUP.md` — environment setup and startup instructions.
- `REVIEW.md` — starter defects, symptoms, and fixes.
- `ISSUE_ANALYSIS.md` — review and testing approach.
- `IMPLEMENTATION_NOTES.md` — design choices and verification notes.
- `DECISIONS.md` — answers to the assignment’s five design questions.

## Submit
A public Git repository with `app/main.py`, `requirements.txt`, `REVIEW.md`, `DECISIONS.md` and a short `README.md`.
No `.env`, no secrets, no Dockerfile.
