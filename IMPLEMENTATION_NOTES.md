# Implementation and verification notes

## Design choices

The service keeps all application code in `app/main.py`, as required by the assignment. PyMongo is used synchronously with FastAPI. MongoDB stores real instants as BSON datetimes, while the API converts them to and from integer epoch milliseconds.

The attendance natural key is `(emp_code, date)`. A unique MongoDB index enforces that key, so concurrent punch-ins are decided by the database rather than a race-prone pre-check. Punch-out uses an atomic update requiring `punch_out` to still be null. Regularization updates the record and appends history only when the record has not changed concurrently.

Derived fields are calculated centrally: late minutes use IST and the ten-minute grace period; work hours use decimal half-up rounding; overtime handles overnight shifts and the thirty-minute minimum; half-day status uses rounded work hours.

Analytics read stored derived values. Employee and department summaries include joiner rules and no-log employees. The leaderboard uses MongoDB ranking semantics for ties. The trend endpoint returns every requested date, including weekends and empty days, and calculates the moving average over the requested range.

## Verification

The API was checked through Swagger at `/docs`, MongoDB Compass, direct endpoint requests, and the focused local test script. MongoDB Compass confirmed the attendance query uses `IXSCAN` through `emp_code_1_date_-1`. The monthly explain output examined two keys and two documents with no collection scan. The department summary received a `joined_on_1_department_1` index so its period filter can use an index as well.

Before submission, run the seed script only against the development database, start the server, verify `/health`, inspect `/docs`, and run `git status` to confirm `.env`, `.venv`, and generated caches are ignored.
