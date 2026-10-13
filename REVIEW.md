# Starter review

| # | Where | What is wrong | How to notice it | Fix |
|---|---|---|---|---|
| 1 | MongoClient | Naive datetimes and host-local time make timezone behavior machine-dependent. | Run on a UTC machine with an IST midnight punch. | Read timezone-aware UTC BSON dates and explicitly use IST for calendar rules. |
| 2 | Startup | No indexes; duplicates possible and lists scan at scale. | Concurrent inserts; inspect query plans. | Idempotent unique natural-key indexes and compound filter/sort indexes. |
| 3 | health | Reports ready without checking MongoDB. | Unavailable MongoDB still returns 200. | Ping with bounded connection timeout; return 503 on database failure. |
| 4 | EmployeeIn | Missing code, length, email, calendar-date and shift validation. | Invalid code, empty name, February 30 or 25:00 accepted. | Schema constraints and calendar validation return 422. |
| 5 | EmployeeIn | Equal shift start/end accepted despite endpoint restriction. | Create a 09:30-09:30 employee. | Model validator rejects equal times. |
| 6 | create_employee | Check-then-insert races. | Parallel duplicate creates both return 201. | Unique index; catch DuplicateKeyError as 409. |
| 7 | create_employee | created_at is naive and serialized as an ISO string. | Inspect response type. | UTC whole-second datetime stored; integer epoch milliseconds returned. |
| 8 | list_employees | page * page_size skips the first page. | Six samples produce an empty default page. | Skip (page - 1) * page_size. |
| 9 | list_employees | total ignores department filter. | Filter to Engineering and compare total to matching documents. | Count with the same query. |
| 10 | list_employees | Missing emp_code sort. | Insert codes out of order. | Sort in MongoDB ascending by emp_code. |
| 11 | Both lists | Invalid page and page_size accepted. | page=0, page_size=0 or 101. | Query constraints produce 422. |
| 12 | PunchInIn | Coerces timestamp strings/floats; accepts seconds, out-of-range values and null. | punched_at="1783312500000", 1783312500 or null. | Strict bounded integer; only omission defaults to now. |
| 13 | PunchInIn | Arbitrary status accepted. | Punch in with ABSENT. | Restrict to PRESENT, WFH and ON_DUTY. |
| 14 | punch_in | Unknown employee dereferenced. | Unknown emp_code causes 500. | Explicit 404 before using employee fields. |
| 15 | punch_in | Host-local date used instead of IST, without overnight attribution. | 02:00 IST punch for 22:00-06:00 shift. | Assign previous shift date before computing lateness. |
| 16 | punch_in | Milliseconds retained contrary to R1. | Punch at 09:40:00.900. | Truncate input to whole seconds before calculation/storage. |
| 17 | punch_in | Check-then-insert permits duplicate daily records. | Eight identical simultaneous punches. | Unique (emp_code, date) index arbitrates; losers get 409. |
| 18 | compute_late_minutes | Floors before testing grace. | 09:40:01 gives 0 instead of 10. | Compare elapsed seconds > 600, then floor minutes. |
| 19 | compute_late_minutes | Uses punch calendar day rather than overnight shift day. | 02:00 punch is late for previous day's 22:00 start. | Pass attendance date and construct IST shift start. |
| 20 | compute_work_hours | Python float/banker's rounding violates half-up. | 450 seconds (0.125 hours) gives 0.12 instead of 0.13. | Decimal division and ROUND_HALF_UP. |
| 21 | compute_overtime | Counts overtime below 30 minutes. | End 18:30, out 18:59 gives 29 instead of 0. | Apply 30-minute minimum. |
| 22 | compute_overtime | Overnight end placed on wrong day. | 22:00-06:00, out next day 06:40. | Move end to next day; expect 40 minutes. |
| 23 | Attendance responses | Invents id and returns datetime strings. | Inspect punch and list responses. | Hide internal _id; recursively convert instants, including history, to epoch ms. |
| 24 | list_attendance | Loads, sorts and slices all matches in Python. | Memory and latency grow with 100,000 matching records. | MongoDB sort/skip/limit and count_documents. |
| 25 | list_attendance | Missing emp_code tie-breaker. | Same-date rows inserted in reverse code order. | Sort date descending, emp_code ascending. |
| 26 | list_attendance | Invalid dates, reversed ranges and invalid statuses accepted. | February 30, from after to, status=UNKNOWN. | Validate dates/status and range; return 422. |
| 27 | Attendance responses | Missing legacy half_day/history left absent. | Read EMP0002 sample record. | Supply false/empty-array defaults, plus documented nullable/zero defaults. |

Examined and retained: load_dotenv does not override real environment variables; synchronous endpoints run in FastAPI's thread pool and fit synchronous PyMongo; extra request fields are ignored as required for client-supplied derived fields; punch-in initializes history to [] and does not append audit entries. The provided sample_seed.py counts six employees and nine logs, despite README wording about nine documents.

Part B endpoints are implemented in `app/main.py`; the defects above describe only the starter review fixes.
