# How the issues were identified

I compared the starter application with `openapi.yaml`, `DATA_MODEL.md`, and the business rules in the problem statement. I checked both the normal path and the cases most likely to expose defects:

- invalid employee codes, dates, emails, shift times, timestamps, and pagination values;
- IST calendar boundaries and overnight shifts;
- the ten-minute late grace period and whole-minute rounding;
- half-up work-hour rounding and the thirty-minute overtime threshold;
- duplicate employee creation and simultaneous punch-ins;
- records with no history or missing legacy fields;
- filtered totals, sorting, and pagination on larger collections;
- employees with no logs, mid-month joiners, weekend records, ties, and missing trend days;
- MongoDB explain plans and index usage.

The starter had more than twenty defects. The main symptoms were host-local datetime calculations, check-then-insert races, missing validation, incorrect page offsets, incorrect filtered totals, Python-side full-collection sorting, missing response conversion to epoch milliseconds, and incomplete endpoint coverage. Each finding is recorded with its location, observable symptom, and correction in `REVIEW.md`.

The focused verification script is `tests/check_starter.py`. It exercises validation, concurrency, pagination, IST handling, overnight dates, rounding, nested timestamp conversion, index usage, and database outage behavior.
