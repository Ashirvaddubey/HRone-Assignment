# Candidate kit

# Arifects
<img width="1427" height="835" alt="image" src="https://github.com/user-attachments/assets/6e6b1986-9da4-4c0b-b1a1-1d05fb41402a" />
<img width="1425" height="830" alt="image" src="https://github.com/user-attachments/assets/7d93aa92-0980-417c-8e43-3ca2fbd648cd" />
<img width="1350" height="719" alt="image" src="https://github.com/user-attachments/assets/6dbd2369-d90e-4251-b60e-ac24ccf0b613" />
<img width="1079" height="702" alt="image" src="https://github.com/user-attachments/assets/a99a6ecb-f998-4e69-a02f-64ca5a3a0712" />
<img width="1060" height="685" alt="image" src="https://github.com/user-attachments/assets/3cdc9968-fdd0-451c-aaa5-a3e168c7b061" />
## Example of exceution:-
MongoDB Query Execution Analysis

This section documents the MongoDB execution plan for the employee_monthly endpoint, including index selection, execution statistics, and query performance.

1. Query Details
Property	Value
Endpoint	employee_monthly
Collection	attendance_logs
Database	attendance_assignment_dev
Employee Code	EMP0001
Date Range	July 1–31, 2026
MongoDB Version	8.0.3
2. Aggregation Query
db.attendance_logs.aggregate([
  {
    $match: {
      emp_code: "EMP0001",
      date: {
        $gte: "2026-07-01",
        $lte: "2026-07-31"
      }
    }
  }
]);

3. Winning Execution Plan

MongoDB selected the compound index emp_code_1_date_-1 to find attendance records for the specified employee and date range.

FETCH
└── IXSCAN
    └── Index: emp_code_1_date_-1

IXSCAN: Scans the index for matching records.
FETCH: Retrieves the matching documents from the collection.
4. Index Used
{
  emp_code: 1,
  date: -1
}


Index name: emp_code_1_date_-1

The compound index supports an equality condition on emp_code and a range condition on date.

5. Execution Statistics
Metric	Result
Execution Success	true
Documents Returned	2
Index Keys Examined	2
Documents Examined	2
Execution Time	0 ms
Index Seeks	1
Winning Plan Stage	FETCH
Index Scan Stage	IXSCAN
6. Index Comparison

MongoDB evaluated three candidate indexes.

Index Name	Planner Decision
emp_code_1_date_-1	Selected
date_-1_emp_code_1	Rejected
emp_code_1_status_1_date_-1	Rejected

The selected index matches the employee equality filter and date-range condition. The query planner chose this index over the other candidates for this execution.

7. Performance Analysis

The query returned 2 documents, examined 2 index keys, and examined 2 documents.

Index efficiency: Two index keys were examined for two returned documents.
Document efficiency: Only the two matching documents were examined.
Execution time: MongoDB reported 0 ms; this is a measured execution result, not a guarantee of zero processing time.
Index usage: The query used an index scan rather than a collection scan.

These results indicate an efficient execution plan for the tested query and dataset. Additional testing with larger datasets is recommended to evaluate performance under realistic workloads.

8. Conclusion

The employee_monthly endpoint uses the compound index emp_code_1_date_-1 to retrieve attendance records for a specific employee within a monthly date range.

The execution statistics show that two index keys and two documents were examined to return two results. The selected index is appropriate for this query pattern based on the observed execution plan.

Note: Execution statistics reflect the tested query and dataset. Actual performance may vary with data volume, distribution, and workload.





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
