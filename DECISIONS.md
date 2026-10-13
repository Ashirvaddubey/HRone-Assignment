# DECISIONS.md  (about 150-200 words in total - plain language, your own words)

1. **Indexes.** Which indexes did you create, and which query or guarantee does each one serve? Which one did you consider and reject?
2. **Punch-in race.** Two identical punch-in requests arrive at the same instant. Walk through exactly what happens in your code.
3. **Ties.** Two employees are tied on late minutes at the cutoff of `limit`. What does your leaderboard return, and why?
4. **Headcount.** How does your department summary make sure employees with zero logs are counted?
5. **One thing you would change** if this had to serve 100x the data.
# Implementation decisions

Indexes include unique `emp_code` and unique `(emp_code, date)` keys, plus compound indexes for employee/date and status/date filters. The unique attendance key is the concurrency control for punch-in: simultaneous requests race at the database, one insert succeeds, and duplicate-key errors become 409 responses. Punch-out uses an atomic update that requires `punch_out: null`, so only one concurrent request can close a record.

The late leaderboard aggregates stored late minutes, joins employees, and uses standard competition ranking. The limit is applied to the rank, so ties at the cutoff are all returned. Department summaries start from employees whose `joined_on` is before the month end; the lookup means an employee with no logs still contributes to headcount, while log metrics are aggregated over records.

For much larger data I would keep the same indexed filters, move analytics to pre-aggregated daily summaries, and consider sharding attendance by employee/date. The API would retain the same natural keys and atomic updates.
