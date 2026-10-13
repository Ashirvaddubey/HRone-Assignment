# Candidate kit

# Arifects
<img width="1427" height="835" alt="image" src="https://github.com/user-attachments/assets/6e6b1986-9da4-4c0b-b1a1-1d05fb41402a" />
<img width="1425" height="830" alt="image" src="https://github.com/user-attachments/assets/7d93aa92-0980-417c-8e43-3ca2fbd648cd" />
<img width="1350" height="719" alt="image" src="https://github.com/user-attachments/assets/6dbd2369-d90e-4251-b60e-ac24ccf0b613" />
<img width="1079" height="702" alt="image" src="https://github.com/user-attachments/assets/a99a6ecb-f998-4e69-a02f-64ca5a3a0712" />
<img width="1060" height="685" alt="image" src="https://github.com/user-attachments/assets/3cdc9968-fdd0-451c-aaa5-a3e168c7b061" />
response :-{
  "endpoint": "employee_monthly",
  "collection": "attendance_logs",
  "explain": {
    "explainVersion": "1",
    "queryPlanner": {
      "namespace": "attendance_assignment_dev.attendance_logs",
      "parsedQuery": {
        "$and": [
          {
            "emp_code": {
              "$eq": "EMP0001"
            }
          },
          {
            "date": {
              "$lte": "2026-07-31"
            }
          },
          {
            "date": {
              "$gte": "2026-07-01"
            }
          }
        ]
      },
      "indexFilterSet": false,
      "queryHash": "17703E5F",
      "planCacheKey": "A76C6602",
      "optimizationTimeMillis": 0,
      "optimizedPipeline": true,
      "maxIndexedOrSolutionsReached": false,
      "maxIndexedAndSolutionsReached": false,
      "maxScansToExplodeReached": false,
      "prunedSimilarIndexes": false,
      "winningPlan": {
        "isCached": false,
        "stage": "FETCH",
        "inputStage": {
          "stage": "IXSCAN",
          "keyPattern": {
            "emp_code": 1,
            "date": -1
          },
          "indexName": "emp_code_1_date_-1",
          "isMultiKey": false,
          "multiKeyPaths": {
            "emp_code": [],
            "date": []
          },
          "isUnique": true,
          "isSparse": false,
          "isPartial": false,
          "indexVersion": 2,
          "direction": "forward",
          "indexBounds": {
            "emp_code": [
              "[\"EMP0001\", \"EMP0001\"]"
            ],
            "date": [
              "[\"2026-07-31\", \"2026-07-01\"]"
            ]
          }
        }
      },
      "rejectedPlans": [
        {
          "isCached": false,
          "stage": "FETCH",
          "inputStage": {
            "stage": "IXSCAN",
            "keyPattern": {
              "date": -1,
              "emp_code": 1
            },
            "indexName": "date_-1_emp_code_1",
            "isMultiKey": false,
            "multiKeyPaths": {
              "date": [],
              "emp_code": []
            },
            "isUnique": false,
            "isSparse": false,
            "isPartial": false,
            "indexVersion": 2,
            "direction": "forward",
            "indexBounds": {
              "date": [
                "[\"2026-07-31\", \"2026-07-01\"]"
              ],
              "emp_code": [
                "[\"EMP0001\", \"EMP0001\"]"
              ]
            }
          }
        },
        {
          "isCached": false,
          "stage": "FETCH",
          "inputStage": {
            "stage": "IXSCAN",
            "keyPattern": {
              "emp_code": 1,
              "status": 1,
              "date": -1
            },
            "indexName": "emp_code_1_status_1_date_-1",
            "isMultiKey": false,
            "multiKeyPaths": {
              "emp_code": [],
              "status": [],
              "date": []
            },
            "isUnique": false,
            "isSparse": false,
            "isPartial": false,
            "indexVersion": 2,
            "direction": "forward",
            "indexBounds": {
              "emp_code": [
                "[\"EMP0001\", \"EMP0001\"]"
              ],
              "status": [
                "[MinKey, MaxKey]"
              ],
              "date": [
                "[\"2026-07-31\", \"2026-07-01\"]"
              ]
            }
          }
        }
      ]
    },
    "executionStats": {
      "executionSuccess": true,
      "nReturned": 2,
      "executionTimeMillis": 0,
      "totalKeysExamined": 2,
      "totalDocsExamined": 2,
      "executionStages": {
        "isCached": false,
        "stage": "FETCH",
        "nReturned": 2,
        "executionTimeMillisEstimate": 0,
        "works": 4,
        "advanced": 2,
        "needTime": 0,
        "needYield": 0,
        "saveState": 0,
        "restoreState": 0,
        "isEOF": 1,
        "docsExamined": 2,
        "alreadyHasObj": 0,
        "inputStage": {
          "stage": "IXSCAN",
          "nReturned": 2,
          "executionTimeMillisEstimate": 0,
          "works": 3,
          "advanced": 2,
          "needTime": 0,
          "needYield": 0,
          "saveState": 0,
          "restoreState": 0,
          "isEOF": 1,
          "keyPattern": {
            "emp_code": 1,
            "date": -1
          },
          "indexName": "emp_code_1_date_-1",
          "isMultiKey": false,
          "multiKeyPaths": {
            "emp_code": [],
            "date": []
          },
          "isUnique": true,
          "isSparse": false,
          "isPartial": false,
          "indexVersion": 2,
          "direction": "forward",
          "indexBounds": {
            "emp_code": [
              "[\"EMP0001\", \"EMP0001\"]"
            ],
            "date": [
              "[\"2026-07-31\", \"2026-07-01\"]"
            ]
          },
          "keysExamined": 2,
          "seeks": 1,
          "dupsTested": 0,
          "dupsDropped": 0
        }
      }
    },
    "command": {
      "aggregate": "attendance_logs",
      "pipeline": [
        {
          "$match": {
            "emp_code": "EMP0001",
            "date": {
              "$gte": "2026-07-01",
              "$lte": "2026-07-31"
            }
          }
        }
      ],
      "cursor": {},
      "$db": "attendance_assignment_dev"
    },
    "serverInfo": {
      "host": "DESKTOP-VS9143U",
      "port": 27017,
      "version": "8.0.3",
      "gitVersion": "89d97f2744a2b9851ddfb51bdf22f687562d9b06"
    },
    "serverParameters": {
      "internalQueryFacetBufferSizeBytes": 104857600,
      "internalQueryFacetMaxOutputDocSizeBytes": 104857600,
      "internalLookupStageIntermediateDocumentMaxSizeBytes": 104857600,
      "internalDocumentSourceGroupMaxMemoryBytes": 104857600,
      "internalQueryMaxBlockingSortMemoryUsageBytes": 104857600,
      "internalQueryProhibitBlockingMergeOnMongoS": 0,
      "internalQueryMaxAddToSetBytes": 104857600,
      "internalDocumentSourceSetWindowFieldsMaxMemoryBytes": 104857600,
      "internalQueryFrameworkControl": "trySbeRestricted",
      "internalQueryPlannerIgnoreIndexWithCollationForRegex": 1
    },
    "ok": 1
  }
}






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
