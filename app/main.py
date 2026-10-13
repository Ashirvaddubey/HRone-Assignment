"""HR attendance API; run with uvicorn app.main:app from candidate_kit."""
import os
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Annotated, Literal, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator, model_validator
from pymongo import MongoClient, ReturnDocument
from pymongo.errors import DuplicateKeyError, PyMongoError

load_dotenv(override=False)
client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"),
                     tz_aware=True, serverSelectionTimeoutMS=3000, connectTimeoutMS=3000)
db = client[os.getenv("MONGO_DB", "attendance_db")]
UTC = timezone.utc
IST = timezone(timedelta(hours=5, minutes=30))
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
Status = Literal["PRESENT", "ABSENT", "LEAVE", "WFH", "ON_DUTY"]
EpochMillis = Annotated[int, Field(strict=True, ge=100000000000, le=4102444800000)]
CalendarDate = Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$")]
ShiftTime = Annotated[str, Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")]
Page = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]


@asynccontextmanager
async def lifespan(app):
    # Unique indexes arbitrate concurrent inserts across processes too.
    db.employees.create_index([("emp_code", 1)], unique=True)
    db.employees.create_index([("department", 1), ("emp_code", 1)])
    db.employees.create_index([("joined_on", 1), ("department", 1)])
    db.attendance_logs.create_index([("emp_code", 1), ("date", -1)], unique=True)
    db.attendance_logs.create_index([("date", -1), ("emp_code", 1)])
    db.attendance_logs.create_index([("status", 1), ("date", -1), ("emp_code", 1)])
    db.attendance_logs.create_index([("emp_code", 1), ("status", 1), ("date", -1)])
    yield
    client.close()


app = FastAPI(title="Employee Attendance & Analytics API", version="2.0.0", lifespan=lifespan)


def instant(milliseconds=None):
    """UTC instant truncated before calculations and storage (R1)."""
    if milliseconds is None:
        return datetime.now(UTC).replace(microsecond=0)
    return EPOCH + timedelta(seconds=milliseconds // 1000)


def to_api(value):
    """Convert BSON dates everywhere, including nested history changes."""
    if isinstance(value, datetime):
        delta = value.astimezone(UTC) - EPOCH
        return (delta.days * 86400 + delta.seconds) * 1000 + delta.microseconds // 1000
    if isinstance(value, dict):
        return {key: to_api(item) for key, item in value.items() if key != "_id"}
    if isinstance(value, list):
        return [to_api(item) for item in value]
    return value


def attendance_response(doc):
    defaults = {"punch_in": None, "punch_out": None, "work_hours": None,
                "late_minutes": 0, "overtime_minutes": 0, "half_day": False, "history": []}
    return to_api({**defaults, **doc})


def attendance_date(punch_in, shift_start, shift_end):
    local = punch_in.astimezone(IST)
    day = local.date()
    if shift_end <= shift_start and local.strftime("%H:%M:%S") < shift_end + ":00":
        day -= timedelta(days=1)
    return day.isoformat()


def shift_instant(date_str, clock):
    return datetime.fromisoformat(date_str + "T" + clock).replace(tzinfo=IST)


def compute_late_minutes(punch_in, shift_start, date_str=None):
    day = date_str or punch_in.astimezone(IST).date().isoformat()
    seconds = int((punch_in - shift_instant(day, shift_start)).total_seconds())
    return seconds // 60 if seconds > 600 else 0


def compute_work_hours(punch_in, punch_out):
    seconds = int((punch_out - punch_in).total_seconds())
    return float((Decimal(seconds) / Decimal(3600)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def compute_overtime(punch_out, shift_end, date_str, shift_start="00:00"):
    end = shift_instant(date_str, shift_end)
    if shift_end <= shift_start:
        end += timedelta(days=1)
    minutes = int((punch_out - end).total_seconds()) // 60
    return minutes if minutes >= 30 else 0


class EmployeeIn(BaseModel):
    emp_code: Annotated[str, Field(pattern=r"^EMP\d{4,6}$")]
    name: Annotated[str, Field(min_length=1, max_length=100)]
    email: Annotated[str, Field(max_length=120, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")]
    department: Annotated[str, Field(min_length=1, max_length=50)]
    shift_start: ShiftTime = "09:30"
    shift_end: ShiftTime = "18:30"
    joined_on: CalendarDate

    @field_validator("joined_on")
    @classmethod
    def valid_date(cls, value):
        date.fromisoformat(value)
        return value

    @model_validator(mode="after")
    def different_shift_times(self):
        if self.shift_start == self.shift_end:
            raise ValueError("shift_start must differ from shift_end")
        return self


class PunchInIn(BaseModel):
    emp_code: str
    punched_at: EpochMillis = Field(default_factory=lambda: int(datetime.now(UTC).timestamp()) * 1000)
    status: Literal["PRESENT", "WFH", "ON_DUTY"] = "PRESENT"

class PunchOutIn(BaseModel):
    emp_code: str
    punched_at: EpochMillis = Field(default_factory=lambda: int(datetime.now(UTC).timestamp()) * 1000)

class RegularizeIn(BaseModel):
    status: Optional[Status] = None
    punch_in: Optional[EpochMillis] = None
    punch_out: Optional[EpochMillis] = None
    reason: Annotated[str, Field(min_length=5, max_length=200)]
    regularized_by: Annotated[str, Field(min_length=1, max_length=50)]


@app.get("/health")
def health():
    try:
        client.admin.command("ping")
    except PyMongoError:
        raise HTTPException(503, "MongoDB is unavailable")
    return {"status": "ok"}


@app.post("/employees", status_code=201)
def create_employee(body: EmployeeIn):
    doc = {**body.model_dump(), "created_at": instant()}
    try:
        db.employees.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(409, "emp_code already exists")
    return to_api(doc)


@app.get("/employees")
def list_employees(department: Optional[str] = None, page: Page = 1, page_size: PageSize = 20):
    query = {} if department is None else {"department": department}
    items = db.employees.find(query, {"_id": 0}).sort("emp_code", 1).skip((page - 1) * page_size).limit(page_size)
    return {"items": [to_api(doc) for doc in items], "total": db.employees.count_documents(query),
            "page": page, "page_size": page_size}


@app.post("/attendance/punch-in", status_code=201)
def punch_in(body: PunchInIn):
    employee = db.employees.find_one({"emp_code": body.emp_code})
    if employee is None:
        raise HTTPException(404, "employee not found")
    timestamp = instant(body.punched_at)
    day = attendance_date(timestamp, employee["shift_start"], employee["shift_end"])
    doc = {"emp_code": body.emp_code, "date": day, "status": body.status,
           "punch_in": timestamp, "punch_out": None, "work_hours": None,
           "late_minutes": compute_late_minutes(timestamp, employee["shift_start"], day),
           "overtime_minutes": 0, "half_day": False, "history": []}
    try:
        db.attendance_logs.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(409, "already punched in for this date")
    return attendance_response(doc)


def attendance_filter(emp_code, date_from, date_to, status):
    for value in (date_from, date_to):
        if value is not None:
            try:
                date.fromisoformat(value)
            except ValueError:
                raise HTTPException(422, [{"loc": ["query", "date"], "msg": "invalid calendar date", "type": "value_error"}])
    if date_from and date_to and date_from > date_to:
        raise HTTPException(422, [{"loc": ["query", "date_to"], "msg": "date_to precedes date_from", "type": "value_error"}])
    query = {}
    if emp_code is not None:
        query["emp_code"] = emp_code
    if date_from is not None or date_to is not None:
        query["date"] = {}
        if date_from is not None:
            query["date"]["$gte"] = date_from
        if date_to is not None:
            query["date"]["$lte"] = date_to
    if status is not None:
        query["status"] = status
    return query


@app.get("/attendance")
def list_attendance(emp_code: Optional[str] = None, date_from: Optional[CalendarDate] = None,
                    date_to: Optional[CalendarDate] = None, status: Optional[Status] = None,
                    page: Page = 1, page_size: PageSize = 20):
    query = attendance_filter(emp_code, date_from, date_to, status)
    items = db.attendance_logs.find(query, {"_id": 0}).sort([("date", -1), ("emp_code", 1)]).skip((page - 1) * page_size).limit(page_size)
    return {"items": [attendance_response(doc) for doc in items], "total": db.attendance_logs.count_documents(query),
            "page": page, "page_size": page_size}


@app.post("/attendance/punch-out")
def punch_out(body: PunchOutIn):
    emp = db.employees.find_one({"emp_code": body.emp_code})
    if not emp: raise HTTPException(404, "employee not found")
    ts = instant(body.punched_at)
    doc = db.attendance_logs.find_one({"emp_code": body.emp_code, "punch_in": {"$lte": ts}}, sort=[("punch_in", -1)])
    if not doc: raise HTTPException(404, "no punch-in found")
    if doc.get("punch_out") is not None: raise HTTPException(409, "already punched out")
    if ts <= doc["punch_in"] or ts > doc["punch_in"] + timedelta(hours=24): raise HTTPException(422, "invalid punch-out time")
    work = compute_work_hours(doc["punch_in"], ts)
    overtime = compute_overtime(ts, emp["shift_end"], doc["date"], emp["shift_start"])
    half = work < 4.50
    updated = db.attendance_logs.find_one_and_update(
        {"_id": doc["_id"], "punch_out": None},
        {"$set": {"punch_out": ts, "work_hours": work, "overtime_minutes": overtime, "half_day": half}},
        return_document=ReturnDocument.AFTER)
    if updated is None: raise HTTPException(409, "already punched out")
    return attendance_response(updated)

@app.patch("/attendance/{emp_code}/{date}")
def regularize(emp_code: str, date: CalendarDate, body: RegularizeIn):
    day = date
    try: datetime.fromisoformat(day)
    except ValueError: raise HTTPException(422, "invalid date")
    emp = db.employees.find_one({"emp_code": emp_code})
    doc = db.attendance_logs.find_one({"emp_code": emp_code, "date": day})
    if not emp or not doc: raise HTTPException(404, "record not found")
    old = {k: doc.get(k) for k in ("status", "punch_in", "punch_out", "work_hours", "late_minutes", "overtime_minutes", "half_day")}
    status = body.status or doc.get("status")
    pin = instant(body.punch_in) if body.punch_in is not None else doc.get("punch_in")
    pout = instant(body.punch_out) if body.punch_out is not None else doc.get("punch_out")
    if status in ("ABSENT", "LEAVE"):
        if body.punch_in is not None or body.punch_out is not None: raise HTTPException(422, "absence cannot have punch times")
        pin = pout = None
    elif pin is None: raise HTTPException(422, "presence requires punch_in")
    if pin is not None and attendance_date(pin, emp["shift_start"], emp["shift_end"]) != day: raise HTTPException(422, "punch_in date mismatch")
    if pout is not None and (pin is None or pout <= pin or pout > pin + timedelta(hours=24)): raise HTTPException(422, "invalid punch_out")
    late = compute_late_minutes(pin, emp["shift_start"], day) if pin else 0
    work = compute_work_hours(pin, pout) if pin and pout else None
    overtime = compute_overtime(pout, emp["shift_end"], day, emp["shift_start"]) if pin and pout else 0
    half = bool(work is not None and work < 4.5)
    new = {"status": status, "punch_in": pin, "punch_out": pout, "work_hours": work, "late_minutes": late, "overtime_minutes": overtime, "half_day": half}
    changes = {k: {"from": old[k], "to": v} for k, v in new.items() if old[k] != v}
    if not changes: raise HTTPException(422, "nothing changed")
    entry = {"at": instant(), "by": body.regularized_by, "reason": body.reason, "changes": changes}
    updated = db.attendance_logs.find_one_and_update({"_id": doc["_id"], "history": doc.get("history", [])}, {"$set": new, "$push": {"history": entry}}, return_document=ReturnDocument.AFTER)
    if updated is None: raise HTTPException(409, "record changed concurrently")
    return attendance_response(updated)

def month_bounds(month):
    try:
        y, m = map(int, month.split("-")); start = date(y,m,1)
        end = date(y+1,1,1) if m == 12 else date(y,m+1,1)
        return start.isoformat(), (end-timedelta(days=1)).isoformat()
    except Exception: raise HTTPException(422, "invalid month")

@app.get("/analytics/employees/{emp_code}/monthly")
def employee_monthly(emp_code: str, month: Annotated[str, Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")]):
    emp = db.employees.find_one({"emp_code": emp_code})
    if not emp: raise HTTPException(404, "employee not found")
    start, end = month_bounds(month); first=date.fromisoformat(max(start, emp["joined_on"])); last=date.fromisoformat(end)
    working = sum((first+timedelta(days=i)).weekday()<5 for i in range(max(0,(last-first).days+1)))
    pipe=[{"$match":{"emp_code":emp_code,"date":{"$gte":start,"$lte":end}}},{"$group":{"_id":None,"present":{"$sum":{"$cond":[{"$in":["$status",["PRESENT","WFH","ON_DUTY"]]},{"$cond":[{"$and":[{"$lt":[{"$dayOfWeek":{"$dateFromString":{"dateString":"$date"}}},7]},{"$gt":[{"$dayOfWeek":{"$dateFromString":{"dateString":"$date"}}},1]}]}, {"$cond":["$half_day",0.5,1]},0]},0]}},"leave":{"$sum":{"$cond":[{"$eq":["$status","LEAVE"]},1,0]}},"late":{"$sum":{"$cond":[{"$gt":["$late_minutes",0]},1,0]}},"late_min":{"$sum":{"$ifNull":["$late_minutes",0]}},"ot":{"$sum":{"$ifNull":["$overtime_minutes",0]}}}}]
    x=next(iter(db.attendance_logs.aggregate(pipe)),{})
    present=x.get("present",0); return {"emp_code":emp_code,"month":month,"working_days":working,"present_days":present,"leave_days":x.get("leave",0),"late_count":x.get("late",0),"total_late_minutes":x.get("late_min",0),"total_overtime_minutes":x.get("ot",0),"attendance_pct":round(present/working*100,2) if working else None}

@app.get("/analytics/departments/summary")
def department_summary(month: Annotated[str, Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")], department: Optional[str]=None):
    start,end=month_bounds(month); q={"joined_on":{"$lte":end}}; q.update({"department":department} if department else {})
    emps=list(db.employees.find(q,{"_id":0})); ids={e["emp_code"] for e in emps}; groups={}
    for e in emps: groups.setdefault(e["department"],{"department":e["department"],"headcount":0})["headcount"]+=1
    pipe=[{"$match":{"date":{"$gte":start,"$lte":end},"emp_code":{"$in":list(ids)}}},{"$lookup":{"from":"employees","localField":"emp_code","foreignField":"emp_code","as":"e"}},{"$unwind":"$e"},{"$set":{"dow":{"$dayOfWeek":{"$dateFromString":{"dateString":"$date"}}}}},{"$group":{"_id":"$e.department","present":{"$sum":{"$cond":[{"$and":[{"$in":["$status",["PRESENT","WFH","ON_DUTY"]]},{"$gt":["$dow",1]},{"$lt":["$dow",7]}]},{"$cond":["$half_day",0.5,1]},0]}},"late":{"$sum":{"$cond":[{"$gt":[{"$ifNull":["$late_minutes",0]},0]},1,0]}},"late_min":{"$sum":{"$ifNull":["$late_minutes",0]}},"leave":{"$sum":{"$cond":[{"$eq":["$status","LEAVE"]},1,0]}},"onduty":{"$sum":{"$cond":[{"$eq":["$status","ON_DUTY"]},1,0]}},"hours":{"$avg":{"$cond":[{"$and":[{"$in":["$status",["PRESENT","WFH","ON_DUTY"]]},{"$ne":["$work_hours",None]}]},"$work_hours",None]}}}}]
    for x in db.attendance_logs.aggregate(pipe):
        g=groups.get(x["_id"]); g.update({"present_days":x.get("present",0),"avg_work_hours":round(x["hours"],2) if x.get("hours") is not None else None,"late_count":x.get("late",0),"total_late_minutes":x.get("late_min",0),"leave_count":x.get("leave",0),"on_duty_count":x.get("onduty",0)})
    for g in groups.values(): g.setdefault("present_days",0); g.setdefault("avg_work_hours",None); g.setdefault("late_count",0); g.setdefault("total_late_minutes",0); g.setdefault("leave_count",0); g.setdefault("on_duty_count",0)
    return {"month":month,"items":sorted(groups.values(),key=lambda x:x["department"])}

@app.get("/analytics/leaderboard/late")
def leaderboard(month: Annotated[str, Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")], limit: Annotated[int,Query(ge=1,le=50)]=10, department: Optional[str]=None):
    start,end=month_bounds(month); pipe=[{"$match":{"date":{"$gte":start,"$lte":end},"late_minutes":{"$gt":0}}},{"$group":{"_id":"$emp_code","total":{"$sum":"$late_minutes"},"count":{"$sum":1}}},{"$lookup":{"from":"employees","localField":"_id","foreignField":"emp_code","as":"e"}},{"$unwind":"$e"}]
    if department: pipe.append({"$match":{"e.department":department}})
    pipe += [{"$sort":{"total":-1,"_id":1}},{"$setWindowFields":{"sortBy":{"total":-1},"output":{"rank":{"$rank":{}}}}},{"$match":{"rank":{"$lte":limit}}},{"$project":{"_id":0,"rank":1,"emp_code":"$_id","name":"$e.name","department":"$e.department","total_late_minutes":"$total","late_count":"$count"}}]
    return {"month":month,"items":list(db.attendance_logs.aggregate(pipe))}

@app.get("/analytics/departments/{department}/trend")
def department_trend(department: str, from_: Annotated[str, Query(alias="from")], to: str):
    try: a=date.fromisoformat(from_); b=date.fromisoformat(to)
    except ValueError: raise HTTPException(422,"invalid date")
    if b<a or (b-a).days>91: raise HTTPException(422,"invalid range")
    if not db.employees.find_one({"department":department}): raise HTTPException(404,"department not found")
    emps = list(db.employees.find({"department": department}, {"_id": 0, "emp_code": 1, "joined_on": 1}))
    ids = [e["emp_code"] for e in emps]
    start_dt=datetime.combine(a, datetime.min.time(), tzinfo=UTC); end_dt=datetime.combine(b, datetime.min.time(), tzinfo=UTC)
    pipeline = [
        {"$match": {"emp_code": {"$in": ids}, "date": {"$gte": from_, "$lte": to}}},
        {"$project": {"date": {"$dateFromString": {"dateString": "$date"}}, "status": 1, "half_day": 1, "late_minutes": 1}},
        {"$group": {"_id": "$date", "present_count": {"$sum": {"$cond": [{"$in": ["$status", ["PRESENT", "WFH", "ON_DUTY"]]}, {"$cond": ["$half_day", 0.5, 1]}, 0]}}, "late_count": {"$sum": {"$cond": [{"$gt": [{"$ifNull": ["$late_minutes", 0]}, 0]}, 1, 0]}}}},
        {"$project": {"_id": 0, "date": "$_id", "present_count": 1, "late_count": 1}},
        {"$densify": {"field": "date", "range": {"step": 1, "unit": "day", "bounds": [start_dt, end_dt]}}},
        {"$set": {"present_count": {"$ifNull": ["$present_count", 0]}, "late_count": {"$ifNull": ["$late_count", 0]}, "is_working_day": {"$in": [{"$dayOfWeek": "$date"}, [2, 3, 4, 5, 6]]}}},
        {"$setWindowFields": {"sortBy": {"date": 1}, "output": {"moving_avg_7d": {"$avg": "$present_count", "window": {"documents": [-6, 0]}}}}},
        {"$sort": {"date": 1}}
    ]
    rows=list(db.aggregate(pipeline))
    out=[]
    for row in rows:
        ds=row["date"].date().isoformat(); head=sum(e["joined_on"] <= ds for e in emps); working=row["is_working_day"]
        rate=round(row["present_count"]/head,4) if working and head else (0.0 if working else None)
        avg=row.get("moving_avg_7d")
        out.append({"date":ds,"is_working_day":working,"headcount":head,"present_count":row["present_count"],"late_count":row["late_count"],"attendance_rate":rate,"moving_avg_7d":round(avg,4) if avg is not None else None})
    for i, item in enumerate(out):
        window=[x["attendance_rate"] for x in out[max(0, i-6):i+1] if x["attendance_rate"] is not None]
        item["moving_avg_7d"] = round(sum(window)/len(window), 4) if window else None
    return {"department":department,"items":out}

@app.get("/admin/explain/{endpoint}")
def explain_endpoint(endpoint: str, emp_code: Optional[str]=None, month: Optional[str]=None, department: Optional[str]=None, date_from: Optional[str]=None, date_to: Optional[str]=None, status: Optional[Status]=None, page: Page=1, page_size: PageSize=20, from_: Optional[str]=Query(None, alias="from"), to: Optional[str]=None):
    allowed={"attendance_list","employee_monthly","department_summary","late_leaderboard","department_trend"}
    if endpoint not in allowed: raise HTTPException(422,"unknown endpoint")
    if endpoint in {"employee_monthly", "late_leaderboard", "department_summary"} and not month:
        raise HTTPException(422, "month is required")
    if endpoint == "employee_monthly" and not emp_code:
        raise HTTPException(422, "emp_code is required")
    if endpoint == "department_trend" and (not department or not from_ or not to):
        raise HTTPException(422, "department, from and to are required")
    if endpoint == "attendance_list":
        query=attendance_filter(emp_code,date_from,date_to,status)
        raw=db.command("explain", {"find":"attendance_logs","filter":query,"sort":{"date":-1,"emp_code":1},"skip":(page-1)*page_size,"limit":page_size}, verbosity="executionStats")
        return {"endpoint":endpoint,"collection":"attendance_logs","explain":raw}
    if endpoint == "employee_monthly":
        start,end=month_bounds(month)
        operation={"aggregate":"attendance_logs","pipeline":[{"$match":{"emp_code":emp_code,"date":{"$gte":start,"$lte":end}}}],"cursor":{}}
    elif endpoint == "department_summary":
        _,end=month_bounds(month)
        operation={"aggregate":"employees","pipeline":[{"$match":{"joined_on":{"$lte":end}, **({"department":department} if department else {})}}],"cursor":{}}
    elif endpoint == "late_leaderboard":
        start,end=month_bounds(month)
        operation={"aggregate":"attendance_logs","pipeline":[{"$match":{"date":{"$gte":start,"$lte":end},"late_minutes":{"$gt":0}}}],"cursor":{}}
    else:
        operation={"aggregate":"attendance_logs","pipeline":[{"$match":{"date":{"$gte":from_,"$lte":to}}}],"cursor":{}}
    raw=db.command("explain", operation, verbosity="executionStats")
    return {"endpoint":endpoint,"collection":operation.get("aggregate"),"explain":raw}
