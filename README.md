# Employee Attendance & Analytics API

FastAPI and MongoDB backend for the HROne attendance assignment. The API supports employee management, attendance events, corrections, analytics, and MongoDB explain output.

## Quick start

Requirements: Python 3.11+ and MongoDB 6.0+.

```powershell
cd D:\dubey\HRoneAssignement\candidate_kit
\.venv\Scripts\python.exe -m pip install -r requirements.txt
\.venv\Scripts\python.exe sample_seed.py
\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000 --reload
```

Open [Swagger UI](http://127.0.0.1:8000/docs). The readiness endpoint is [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health).

The application reads `MONGO_URI` and `MONGO_DB` from the environment. Local development values are documented in `.env.example`; `.env` is ignored by Git.

## Implemented features

- MongoDB readiness check and automatic, idempotent index creation.
- Employee creation with validation, uniqueness, filtering, sorting, and pagination.
- Punch-in with strict epoch-millisecond validation, IST dates, overnight shifts, late-minute calculation, and race-safe uniqueness.
- Attendance listing with employee, date, and status filters backed by indexes.
- Punch-out with atomic closing, half-day calculation, half-up work-hour rounding, and overtime rules.
- Regularization with validation, derived-field recomputation, and append-only audit history.
- Employee monthly summaries, department summaries, late leaderboard ranking, and department trends.
- Explain output for the supported query and aggregation operations.

## API routes

The complete contract is in `openapi.yaml`. Swagger exposes:

`/health`, `/employees`, `/attendance`, `/attendance/punch-in`, `/attendance/punch-out`, `/attendance/{emp_code}/{date}`, `/analytics/employees/{emp_code}/monthly`, `/analytics/departments/summary`, `/analytics/leaderboard/late`, `/analytics/departments/{department}/trend`, and `/admin/explain/{endpoint}`.

## Verification

The implementation was checked with sample data and focused tests covering invalid input, pagination, IST boundaries, overnight shifts, rounding, concurrent duplicate requests, nested history timestamps, MongoDB availability, and index usage.

Run the local check with the API running:

```powershell
\.venv\Scripts\python.exe tests/check_starter.py
```

MongoDB Compass confirmed `IXSCAN` for the employee/date attendance query and the monthly employee query. The monthly explain output showed two index keys and two documents examined, with no collection scan.

## Artifacts

The following screenshots document the running API, MongoDB collections, indexes, and explain-plan verification:

![Swagger API routes](https://github.com/user-attachments/assets/6e6b1986-9da4-4c0b-b1a1-1d05fb41402a)

![Swagger endpoint testing](https://github.com/user-attachments/assets/7d93aa92-0980-417c-8e43-3ca2fbd648cd)

![MongoDB attendance documents](https://github.com/user-attachments/assets/6dbd2369-d90e-4251-b60e-ac24ccf0b613)

![MongoDB indexes](https://github.com/user-attachments/assets/a99a6ecb-f998-4e69-a02f-64ca5a3a0712)

![MongoDB IXSCAN explain plan](https://github.com/user-attachments/assets/3cdc9968-fdd0-451c-aaa5-a3e168c7b061)

## Documentation

- `SETUP.md` — environment setup and startup instructions.
- `REVIEW.md` — starter defects, symptoms, and fixes.
- `ISSUE_ANALYSIS.md` — review and testing approach.
- `IMPLEMENTATION_NOTES.md` — design choices and verification notes.
- `ENDPOINTS.md` — endpoint-by-endpoint behavior, inputs, errors, and implementation details.
- `DECISIONS.md` — answers to the assignment’s five design questions.
- `DATA_MODEL.md` — MongoDB collections and field conventions.
- `openapi.yaml` — API contract and business rules.

## MongoDB execution example

For `employee_monthly` with `EMP0001` in July 2026, MongoDB selected the compound index `emp_code_1_date_-1`:

```text
FETCH
└── IXSCAN
    └── Index: emp_code_1_date_-1
```

The query returned two records, examined two index keys, examined two documents, and reported no `COLLSCAN`.

## Submission

The repository contains the required application code, `requirements.txt`, `README.md`, `REVIEW.md`, and `DECISIONS.md`. Secrets, `.env`, `.venv`, and generated Python caches are excluded from Git.
