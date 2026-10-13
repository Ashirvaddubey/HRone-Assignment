"""Run with .venv/Scripts/python tests/check_starter.py against localhost:8001.
Set TEST_BASE_URL to use another port. Uses temporary employees;
removes only documents created by this check.
"""
import json
import os
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import main as m

BASE = os.getenv("TEST_BASE_URL", "http://127.0.0.1:8001")


def request(path, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = Request(BASE + path, data=data, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=10) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, json.load(error)


def ms(local):
    return int(datetime.fromisoformat(local).replace(tzinfo=m.IST).timestamp()) * 1000


def run():
    code = next("EMP" + str(n) for n in range(999999, 990000, -1)
                if not m.db.employees.find_one({"emp_code": "EMP" + str(n)}))
    department = "test_" + uuid.uuid4().hex[:12]
    employee = {"emp_code": code, "name": "Check", "email": "check@example.com",
                "department": department, "joined_on": "2026-01-01"}
    created = False
    try:
        assert request('/health') == (200, {"status": "ok"})
        for change in ({"joined_on": "2026-02-30"}, {"shift_start": "25:00"},
                       {"shift_end": "09:30"}, {"email": "bad"}, {"emp_code": "bad"}):
            assert request('/employees', {**employee, **change})[0] == 422
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: request('/employees', employee), range(8)))
        created = any(status == 201 for status, _ in results)
        assert sorted(status for status, _ in results) == [201] + [409] * 7
        response = next(body for status, body in results if status == 201)
        assert isinstance(response['created_at'], int) and '_id' not in response
        status, page = request('/employees?department=' + department)
        assert status == 200 and page['total'] == 1 and page['items'][0]['emp_code'] == code
        for path in ('/employees?page=0', '/attendance?page_size=101',
                     '/attendance?date_from=2026-02-30',
                     '/attendance?date_from=2026-08-01&date_to=2026-07-01',
                     '/attendance?status=UNKNOWN'):
            assert request(path)[0] == 422, path
        for timestamp in (1783312500, '1783312500000', 1783312500000.0, None, True, 4102444800001):
            assert request('/attendance/punch-in', {'emp_code': code, 'punched_at': timestamp})[0] == 422
        assert request('/attendance/punch-in', {'emp_code': code, 'status': 'ABSENT'})[0] == 422
        assert request('/attendance/punch-in', {'emp_code': 'UNKNOWN'})[0] == 404
        punch = {'emp_code': code, 'punched_at': ms('2026-07-20T09:40:01') + 900}
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: request('/attendance/punch-in', punch), range(8)))
        assert sorted(status for status, _ in results) == [201] + [409] * 7
        record = next(body for status, body in results if status == 201)
        assert record['late_minutes'] == 10 and record['punch_in'] == punch['punched_at'] - 900
        assert 'id' not in record and '_id' not in record and record['history'] == []
        assert request('/attendance/punch-in', {'emp_code': code, 'punched_at': ms('2026-07-21T09:40:00') + 900})[1]['late_minutes'] == 0
        for day in ('2026-07-22', '2026-07-23'):
            assert request('/attendance/punch-in', {'emp_code': code, 'punched_at': ms(day + 'T09:30:00')})[0] == 201
        page = request('/attendance?emp_code=' + code + '&page_size=2')[1]
        assert page['total'] == 4 and [row['date'] for row in page['items']] == ['2026-07-23', '2026-07-22']
        m.db.employees.update_one({'emp_code': code}, {'$set': {'shift_start': '22:00', 'shift_end': '06:00'}})
        overnight = request('/attendance/punch-in', {'emp_code': code, 'punched_at': ms('2026-07-25T02:00:00')})[1]
        assert overnight['date'] == '2026-07-24' and overnight['late_minutes'] == 240
        start = m.instant(ms('2026-07-20T09:30:00'))
        assert m.compute_work_hours(start, start + timedelta(seconds=90)) == 0.03
        assert m.compute_work_hours(start, start + timedelta(seconds=450)) == 0.13
        assert m.compute_overtime(m.instant(ms('2026-07-20T18:59:59')), '18:30', '2026-07-20', '09:30') == 0
        assert m.compute_overtime(m.instant(ms('2026-07-21T06:40:00')), '06:00', '2026-07-20', '22:00') == 40
        nested = m.to_api({'history': [{'at': start, 'changes': {'punch_in': {'from': start, 'to': None}}}]})
        assert isinstance(nested['history'][0]['changes']['punch_in']['from'], int)
        assert m.attendance_response({'emp_code': code, 'date': '2026-07-01', 'status': 'ABSENT'})['half_day'] is False
        plan = m.db.command('explain', {'find': 'attendance_logs', 'filter': {},
                            'sort': {'date': -1, 'emp_code': 1}, 'limit': 20}, verbosity='executionStats')
        stages = json.dumps(plan, default=str)
        assert 'IXSCAN' in stages and 'COLLSCAN' not in stages
        original_client = m.client
        class Unavailable:
            @property
            def admin(self):
                raise m.PyMongoError('simulated outage')
        m.client = Unavailable()
        try:
            try:
                m.health()
                raise AssertionError('health accepted an outage')
            except m.HTTPException as error:
                assert error.status_code == 503
        finally:
            m.client = original_client
        print('PASS: validation, pagination, UTC/IST, overnight, rounding, concurrency, serialization, indexed list and outage handling')
    finally:
        if created:
            m.db.attendance_logs.delete_many({'emp_code': code})
            m.db.employees.delete_one({'emp_code': code, 'department': department})
        m.client.close()


if __name__ == '__main__':
    run()
