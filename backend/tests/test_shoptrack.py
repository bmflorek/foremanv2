"""ShopTrack backend regression tests covering auth, jobs, units, vendors,
movements, purchase orders, and the shop board."""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # Fallback to .env file so pytest can still run outside the dev shell
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                break

API = f"{BASE_URL}/api"
DEMO_EMAIL = "shop@demo.com"
DEMO_PASS = "shop1234"


# ---------- fixtures ----------
@pytest.fixture(scope="session")
def token():
    r = requests.post(f"{API}/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASS})
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return r.json()["session_token"]


@pytest.fixture(scope="session")
def h(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def test_job(h):
    """A dedicated job for destructive tests (not 26207)."""
    # try a few numbers starting at 26299 and down
    for num in ["26299", "26298", "26297", "26296", "26295"]:
        r = requests.post(f"{API}/jobs", json={"job_number": num, "name": "TEST_Pytest Job",
                                               "sold_amount": 10000, "status": "active"}, headers=h)
        if r.status_code == 201:
            job = r.json()
            yield job
            requests.delete(f"{API}/jobs/{job['id']}", headers=h)
            return
        if r.status_code != 400:
            pytest.fail(f"Create job failed: {r.status_code} {r.text}")
    pytest.skip("Could not allocate a test job number")


# ---------- auth ----------
class TestAuth:
    def test_health(self):
        r = requests.get(f"{API}/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_unauth_401(self):
        assert requests.get(f"{API}/jobs").status_code == 401
        assert requests.get(f"{API}/auth/me").status_code == 401

    def test_login_success(self):
        r = requests.post(f"{API}/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASS})
        assert r.status_code == 200
        d = r.json()
        assert "session_token" in d and isinstance(d["session_token"], str)
        assert d["user"]["email"] == DEMO_EMAIL

    def test_login_invalid(self):
        r = requests.post(f"{API}/auth/login", json={"email": DEMO_EMAIL, "password": "wrong"})
        assert r.status_code == 401

    def test_me(self, h):
        r = requests.get(f"{API}/auth/me", headers=h)
        assert r.status_code == 200
        assert r.json()["email"] == DEMO_EMAIL

    def test_register_and_logout(self):
        email = f"TEST_{uuid.uuid4().hex[:8]}@example.com"
        r = requests.post(f"{API}/auth/register", json={"email": email, "password": "pw123456", "name": "Test User"})
        assert r.status_code == 200, r.text
        tok = r.json()["session_token"]
        headers = {"Authorization": f"Bearer {tok}"}
        assert requests.get(f"{API}/auth/me", headers=headers).status_code == 200
        assert requests.post(f"{API}/auth/logout", headers=headers).status_code == 200
        # cleanup through DB not possible via API; leaving the test user is acceptable


# ---------- jobs ----------
class TestJobs:
    def test_list_jobs_enriched(self, h):
        r = requests.get(f"{API}/jobs", headers=h)
        assert r.status_code == 200
        jobs = r.json()
        assert isinstance(jobs, list) and len(jobs) >= 1
        j0 = jobs[0]
        assert "budget" in j0 and "unit_counts" in j0
        for k in ["sold_amount", "po_total", "remaining", "over_budget", "percent_used"]:
            assert k in j0["budget"]

    def test_create_job_invalid_number(self, h):
        for bad in ["2620", "abcde", "123456"]:
            r = requests.post(f"{API}/jobs", json={"job_number": bad, "name": "X"}, headers=h)
            assert r.status_code == 422, f"expected 422 for {bad}, got {r.status_code}"

    def test_duplicate_job_number(self, h, test_job):
        r = requests.post(f"{API}/jobs", json={"job_number": test_job["job_number"], "name": "dup"}, headers=h)
        assert r.status_code == 400

    def test_update_and_get_job(self, h, test_job):
        r = requests.put(f"{API}/jobs/{test_job['id']}", json={"customer": "Acme Inc"}, headers=h)
        assert r.status_code == 200
        assert r.json()["customer"] == "Acme Inc"
        r2 = requests.get(f"{API}/jobs/{test_job['id']}", headers=h)
        assert r2.status_code == 200 and r2.json()["customer"] == "Acme Inc"

    def test_cascade_delete(self, h):
        # Create a throwaway job, add a unit and PO, then delete and verify cascade
        r = requests.post(f"{API}/jobs", json={"job_number": "26294", "name": "TEST_cascade",
                                               "sold_amount": 1000, "status": "active"}, headers=h)
        if r.status_code == 400:
            # already exists -> delete it first
            jobs = requests.get(f"{API}/jobs", headers=h).json()
            for j in jobs:
                if j["job_number"] == "26294":
                    requests.delete(f"{API}/jobs/{j['id']}", headers=h)
            r = requests.post(f"{API}/jobs", json={"job_number": "26294", "name": "TEST_cascade",
                                                   "sold_amount": 1000, "status": "active"}, headers=h)
        assert r.status_code == 201
        job = r.json()
        u = requests.post(f"{API}/jobs/{job['id']}/units", json={"unit_number": "W1"}, headers=h).json()
        requests.post(f"{API}/jobs/{job['id']}/purchase-orders",
                      json={"line_items": [{"description": "x", "qty": 1, "unit_cost": 10}]}, headers=h)
        assert requests.delete(f"{API}/jobs/{job['id']}", headers=h).status_code == 200
        assert requests.get(f"{API}/jobs/{job['id']}", headers=h).status_code == 404
        assert requests.get(f"{API}/units/{u['id']}", headers=h).status_code == 404


# ---------- units ----------
class TestUnits:
    def test_unit_normalization_and_type(self, h, test_job):
        cases = [("w1A", "W1a", "window"), ("bf2", "BF2", "bifold"), ("sl3", "SL3", "slider"), ("d4", "D4", "door")]
        for raw, norm, typ in cases:
            r = requests.post(f"{API}/jobs/{test_job['id']}/units", json={"unit_number": raw}, headers=h)
            assert r.status_code == 201, r.text
            assert r.json()["unit_number"] == norm
            assert r.json()["unit_type"] == typ

    def test_unit_custom_type(self, h, test_job):
        r = requests.post(f"{API}/jobs/{test_job['id']}/units", json={"unit_number": "XY1"}, headers=h)
        assert r.status_code == 201
        assert r.json()["unit_type"] == "custom"

    def test_unit_invalid(self, h, test_job):
        r = requests.post(f"{API}/jobs/{test_job['id']}/units", json={"unit_number": "hello"}, headers=h)
        assert r.status_code == 422

    def test_unit_duplicate(self, h, test_job):
        requests.post(f"{API}/jobs/{test_job['id']}/units", json={"unit_number": "W9"}, headers=h)
        r = requests.post(f"{API}/jobs/{test_job['id']}/units", json={"unit_number": "W9"}, headers=h)
        assert r.status_code == 400

    def test_unit_status_update(self, h, test_job):
        u = requests.post(f"{API}/jobs/{test_job['id']}/units", json={"unit_number": "W20"}, headers=h).json()
        r = requests.patch(f"{API}/units/{u['id']}", json={"status": "in_fab"}, headers=h)
        assert r.status_code == 200 and r.json()["status"] == "in_fab"

    def test_cannot_change_status_when_checked_out(self, h, test_job):
        # Need a vendor
        vendors = requests.get(f"{API}/vendors", headers=h).json()
        assert vendors, "need seeded vendor"
        u = requests.post(f"{API}/jobs/{test_job['id']}/units", json={"unit_number": "W30"}, headers=h).json()
        mv = requests.post(f"{API}/movements",
                           json={"unit_id": u["id"], "direction": "out", "vendor_id": vendors[0]["id"]}, headers=h)
        assert mv.status_code == 201, mv.text
        r = requests.patch(f"{API}/units/{u['id']}", json={"status": "complete"}, headers=h)
        assert r.status_code == 400
        # check it back in
        requests.post(f"{API}/movements", json={"unit_id": u["id"], "direction": "in"}, headers=h)


# ---------- vendors ----------
class TestVendors:
    def test_crud(self, h):
        v = requests.post(f"{API}/vendors",
                          json={"name": f"TEST_V_{uuid.uuid4().hex[:6]}", "service": "paint"}, headers=h)
        assert v.status_code == 201
        vid = v.json()["id"]
        upd = requests.put(f"{API}/vendors/{vid}", json={"phone": "555-1234"}, headers=h)
        assert upd.status_code == 200 and upd.json()["phone"] == "555-1234"
        assert requests.delete(f"{API}/vendors/{vid}", headers=h).status_code == 200

    def test_cannot_delete_vendor_in_use(self, h, test_job):
        v = requests.post(f"{API}/vendors", json={"name": f"TEST_V_use_{uuid.uuid4().hex[:4]}", "service": "s"}, headers=h).json()
        u = requests.post(f"{API}/jobs/{test_job['id']}/units", json={"unit_number": "W40"}, headers=h).json()
        requests.post(f"{API}/movements", json={"unit_id": u["id"], "direction": "out", "vendor_id": v["id"]}, headers=h)
        r = requests.delete(f"{API}/vendors/{v['id']}", headers=h)
        assert r.status_code == 400
        requests.post(f"{API}/movements", json={"unit_id": u["id"], "direction": "in"}, headers=h)
        requests.delete(f"{API}/vendors/{v['id']}", headers=h)


# ---------- movements ----------
class TestMovements:
    def test_out_requires_vendor(self, h, test_job):
        u = requests.post(f"{API}/jobs/{test_job['id']}/units", json={"unit_number": "W50"}, headers=h).json()
        r = requests.post(f"{API}/movements", json={"unit_id": u["id"], "direction": "out"}, headers=h)
        assert r.status_code == 400

    def test_in_requires_checked_out(self, h, test_job):
        u = requests.post(f"{API}/jobs/{test_job['id']}/units", json={"unit_number": "W51"}, headers=h).json()
        r = requests.post(f"{API}/movements", json={"unit_id": u["id"], "direction": "in"}, headers=h)
        assert r.status_code == 400

    def test_double_out(self, h, test_job):
        vendors = requests.get(f"{API}/vendors", headers=h).json()
        u = requests.post(f"{API}/jobs/{test_job['id']}/units", json={"unit_number": "W52"}, headers=h).json()
        r1 = requests.post(f"{API}/movements", json={"unit_id": u["id"], "direction": "out", "vendor_id": vendors[0]["id"]}, headers=h)
        assert r1.status_code == 201
        r2 = requests.post(f"{API}/movements", json={"unit_id": u["id"], "direction": "out", "vendor_id": vendors[0]["id"]}, headers=h)
        assert r2.status_code == 400
        requests.post(f"{API}/movements", json={"unit_id": u["id"], "direction": "in"}, headers=h)

    def test_out_in_cycle_and_lists(self, h, test_job):
        vendors = requests.get(f"{API}/vendors", headers=h).json()
        u = requests.post(f"{API}/jobs/{test_job['id']}/units", json={"unit_number": "W53"}, headers=h).json()
        requests.post(f"{API}/movements", json={"unit_id": u["id"], "direction": "out", "vendor_id": vendors[0]["id"]}, headers=h)
        out_list = requests.get(f"{API}/movements/out", headers=h).json()
        assert any(x["id"] == u["id"] for x in out_list)
        for x in out_list:
            if x["id"] == u["id"]:
                assert "job_number" in x and "vendor_name" in x and "days_out" in x
        back = requests.post(f"{API}/movements", json={"unit_id": u["id"], "direction": "in"}, headers=h).json()
        assert back["direction"] == "in"
        after = requests.get(f"{API}/movements/out", headers=h).json()
        assert not any(x["id"] == u["id"] for x in after)
        mvs = requests.get(f"{API}/movements", params={"job_id": test_job["id"]}, headers=h).json()
        assert any(m["unit_id"] == u["id"] and m["direction"] == "out" for m in mvs)


# ---------- purchase orders ----------
class TestPurchaseOrders:
    def test_po_autonumber_and_budget(self, h, test_job):
        p1 = requests.post(f"{API}/jobs/{test_job['id']}/purchase-orders",
                           json={"line_items": [{"description": "a", "qty": 2, "unit_cost": 100}]}, headers=h).json()
        assert p1["po_number"].endswith("-PO-01")
        assert p1["total"] == 200
        assert p1["budget"]["po_total"] == 200
        p2 = requests.post(f"{API}/jobs/{test_job['id']}/purchase-orders",
                           json={"line_items": [{"description": "b", "qty": 1, "unit_cost": 50}]}, headers=h).json()
        assert p2["po_number"].endswith("-PO-02")
        # Over budget
        big = requests.post(f"{API}/jobs/{test_job['id']}/purchase-orders",
                            json={"line_items": [{"description": "big", "qty": 1, "unit_cost": 20000}]}, headers=h).json()
        assert big["budget"]["over_budget"] is True
        assert big["budget"]["remaining"] < 0
        # Cancel one and verify excluded
        upd = requests.put(f"{API}/purchase-orders/{big['id']}", json={"status": "cancelled"}, headers=h).json()
        assert upd["budget"]["over_budget"] is False or upd["budget"]["remaining"] >= 0
        # Update line items recomputes total
        upd2 = requests.put(f"{API}/purchase-orders/{p1['id']}",
                            json={"line_items": [{"description": "a", "qty": 3, "unit_cost": 100}]}, headers=h).json()
        assert upd2["total"] == 300
        # Delete restores budget
        before = requests.get(f"{API}/jobs/{test_job['id']}", headers=h).json()["budget"]["po_total"]
        d = requests.delete(f"{API}/purchase-orders/{p2['id']}", headers=h).json()
        assert d["budget"]["po_total"] == round(before - p2["total"], 2)


# ---------- board ----------
class TestBoard:
    def test_board_columns(self, h):
        r = requests.get(f"{API}/board", headers=h)
        assert r.status_code == 200
        d = r.json()
        cols = {c["status"]: c for c in d["columns"]}
        for s in ["not_started", "in_fab", "out_for_process", "complete"]:
            assert s in cols
        # Each unit should have enrichment keys
        for c in d["columns"]:
            for u in c["units"]:
                assert "job_number" in u and "job_name" in u and "current_vendor_name" in u

    def test_board_excludes_non_active_jobs(self, h):
        # Create a quoted job with a unit and ensure it does not appear
        r = requests.post(f"{API}/jobs", json={"job_number": "26290", "name": "TEST_quoted",
                                               "sold_amount": 100, "status": "quoted"}, headers=h)
        if r.status_code == 400:
            jobs = requests.get(f"{API}/jobs", headers=h).json()
            for j in jobs:
                if j["job_number"] == "26290":
                    requests.delete(f"{API}/jobs/{j['id']}", headers=h)
            r = requests.post(f"{API}/jobs", json={"job_number": "26290", "name": "TEST_quoted",
                                                   "sold_amount": 100, "status": "quoted"}, headers=h)
        assert r.status_code == 201
        job = r.json()
        u = requests.post(f"{API}/jobs/{job['id']}/units", json={"unit_number": "W1"}, headers=h).json()
        board = requests.get(f"{API}/board", headers=h).json()
        for c in board["columns"]:
            assert not any(uu["id"] == u["id"] for uu in c["units"])
        requests.delete(f"{API}/jobs/{job['id']}", headers=h)


# ---------- Issues (iteration 2) ----------
class TestIssues:
    def test_create_list_resolve_reopen_delete(self, h, test_job):
        job_id = test_job["id"]
        # Add a unit so we can test unit_number resolution
        u = requests.post(f"{API}/jobs/{job_id}/units", json={"unit_number": "W1"}, headers=h).json()

        # Missing title -> 422
        r = requests.post(f"{API}/jobs/{job_id}/issues", json={"severity": "low"}, headers=h)
        assert r.status_code == 422

        # Invalid severity -> 400
        r = requests.post(f"{API}/jobs/{job_id}/issues",
                          json={"title": "X", "severity": "critical"}, headers=h)
        assert r.status_code == 400

        # Create valid issue with unit_id
        r = requests.post(f"{API}/jobs/{job_id}/issues",
                          json={"title": "Glass cracked", "description": "d", "severity": "high",
                                "unit_id": u["id"]}, headers=h)
        assert r.status_code == 201
        issue = r.json()
        assert issue["unit_number"] == "W1"
        assert issue["status"] == "open"
        assert issue["severity"] == "high"
        iid = issue["id"]

        # Create a second (no unit)
        r2 = requests.post(f"{API}/jobs/{job_id}/issues",
                           json={"title": "Minor", "severity": "low"}, headers=h)
        assert r2.status_code == 201
        iid2 = r2.json()["id"]

        # List all
        all_list = requests.get(f"{API}/jobs/{job_id}/issues", headers=h).json()
        ids = [i["id"] for i in all_list]
        assert iid in ids and iid2 in ids

        # Filter open
        open_list = requests.get(f"{API}/jobs/{job_id}/issues?status=open", headers=h).json()
        assert all(i["status"] == "open" for i in open_list)
        assert len(open_list) >= 2

        # Job enrichment reflects open_issues count
        job = requests.get(f"{API}/jobs/{job_id}", headers=h).json()
        assert job["open_issues"] >= 2

        # Resolve
        r = requests.patch(f"{API}/issues/{iid}",
                          json={"status": "resolved", "resolution": "Replaced"}, headers=h)
        assert r.status_code == 200
        resolved = r.json()
        assert resolved["status"] == "resolved"
        assert resolved["resolved_at"] is not None
        assert resolved["resolved_by_name"]
        assert resolved["resolution"] == "Replaced"

        # Reopen clears resolved_at/by
        r = requests.patch(f"{API}/issues/{iid}", json={"status": "open"}, headers=h)
        assert r.status_code == 200
        reopened = r.json()
        assert reopened["status"] == "open"
        assert reopened["resolved_at"] is None
        assert reopened["resolved_by_name"] == ""

        # Delete
        r = requests.delete(f"{API}/issues/{iid}", headers=h)
        assert r.status_code == 200
        r = requests.delete(f"{API}/issues/{iid}", headers=h)
        assert r.status_code == 404

        # Cleanup second one
        requests.delete(f"{API}/issues/{iid2}", headers=h)

    def test_delete_job_cascades_issues(self, h):
        # Create a disposable job
        for num in ["26294", "26293", "26292"]:
            r = requests.post(f"{API}/jobs", json={"job_number": num, "name": "TEST_cascade",
                                                   "sold_amount": 0, "status": "active"}, headers=h)
            if r.status_code == 201:
                job = r.json()
                break
        else:
            pytest.skip("No job number available")
        issue = requests.post(f"{API}/jobs/{job['id']}/issues",
                              json={"title": "to-cascade", "severity": "low"}, headers=h).json()
        requests.delete(f"{API}/jobs/{job['id']}", headers=h)
        # Issue should be gone - try to patch
        r = requests.patch(f"{API}/issues/{issue['id']}", json={"status": "resolved"}, headers=h)
        assert r.status_code == 404


# ---------- Approvals (iteration 2) ----------
class TestApprovals:
    def test_approve_revoke_and_invalid_type(self, h, test_job):
        job_id = test_job["id"]

        # Invalid type
        r = requests.put(f"{API}/jobs/{job_id}/approvals/bogus",
                         json={"approved": True, "approved_by": "A"}, headers=h)
        assert r.status_code == 400

        # Baseline: enriched defaults
        job = requests.get(f"{API}/jobs/{job_id}", headers=h).json()
        assert job["approvals_total"] == 3
        assert set(job["approvals"].keys()) == {"drawings", "color_sample", "hardware"}

        # Approve drawings with defaults (empty approved_by -> uses current user name)
        r = requests.put(f"{API}/jobs/{job_id}/approvals/drawings",
                         json={"approved": True, "approved_by": "", "notes": "ok"}, headers=h)
        assert r.status_code == 200
        enriched = r.json()
        assert enriched["approvals"]["drawings"]["approved"] is True
        assert enriched["approvals"]["drawings"]["approved_at"]  # defaulted to today
        assert enriched["approvals"]["drawings"]["approved_by"]  # defaulted to user name
        assert enriched["approvals_done"] == 1

        # Approve color_sample with explicit data
        r = requests.put(f"{API}/jobs/{job_id}/approvals/color_sample",
                         json={"approved": True, "approved_by": "John", "approved_at": "2026-01-15"},
                         headers=h)
        assert r.status_code == 200
        assert r.json()["approvals_done"] == 2

        # Revoke drawings clears approved_at
        r = requests.put(f"{API}/jobs/{job_id}/approvals/drawings",
                         json={"approved": False, "approved_by": ""}, headers=h)
        assert r.status_code == 200
        enriched = r.json()
        assert enriched["approvals"]["drawings"]["approved"] is False
        assert enriched["approvals"]["drawings"]["approved_at"] is None
        assert enriched["approvals_done"] == 1

    def test_old_jobs_have_approval_defaults(self, h):
        jobs = requests.get(f"{API}/jobs", headers=h).json()
        for j in jobs:
            assert "approvals" in j and j["approvals_total"] == 3
            assert set(j["approvals"].keys()) == {"drawings", "color_sample", "hardware"}


# ---------- Board filter (iteration 2) ----------
class TestBoardFilter:
    def test_board_jobs_list_and_filter(self, h, test_job):
        board = requests.get(f"{API}/board", headers=h).json()
        assert "jobs" in board and isinstance(board["jobs"], list)
        job_ids = [j["id"] for j in board["jobs"]]
        assert test_job["id"] in job_ids
        # Each entry has required fields
        for j in board["jobs"]:
            assert set(["id", "job_number", "name"]).issubset(j.keys())

        # Add a unit to test_job
        requests.post(f"{API}/jobs/{test_job['id']}/units",
                      json={"unit_number": "W2"}, headers=h)

        # Filter by test_job id
        filtered = requests.get(f"{API}/board?job_id={test_job['id']}", headers=h).json()
        for col in filtered["columns"]:
            for u in col["units"]:
                assert u["job_id"] == test_job["id"]

        # Unknown job_id -> falls back to all
        fallback = requests.get(f"{API}/board?job_id=does-not-exist", headers=h).json()
        assert fallback["total_units"] >= filtered["total_units"]


# ---------- Vendor stats (iteration 2) ----------
class TestVendorStats:
    def test_vendor_stats_structure_and_trip_cycle(self, h, test_job):
        vendors = requests.get(f"{API}/vendors", headers=h).json()
        assert len(vendors) > 0
        for v in vendors:
            assert "stats" in v
            assert set(["completed_trips", "avg_days_out", "currently_out"]).issubset(v["stats"].keys())
        vendor = vendors[0]
        baseline_trips = vendor["stats"]["completed_trips"]

        # Add a unit, check it out and back in
        unit = requests.post(f"{API}/jobs/{test_job['id']}/units",
                             json={"unit_number": "W3"}, headers=h).json()
        r = requests.post(f"{API}/movements",
                          json={"unit_id": unit["id"], "vendor_id": vendor["id"],
                                "direction": "out", "notes": "t"},
                          headers=h)
        assert r.status_code in (200, 201)

        # While out
        v_now = [v for v in requests.get(f"{API}/vendors", headers=h).json() if v["id"] == vendor["id"]][0]
        assert v_now["stats"]["currently_out"] >= 1

        # Check back in
        r = requests.post(f"{API}/movements",
                          json={"unit_id": unit["id"], "direction": "in", "notes": "back"}, headers=h)
        assert r.status_code in (200, 201)

        v_after = [v for v in requests.get(f"{API}/vendors", headers=h).json() if v["id"] == vendor["id"]][0]
        assert v_after["stats"]["completed_trips"] == baseline_trips + 1
        assert v_after["stats"]["avg_days_out"] is not None



# ---------- Iteration 3: refactor regression (board urgency, digest cron) ----------
def _load_env(key: str) -> str:
    with open("/app/backend/.env") as f:
        for line in f:
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip()
    return ""


class TestBoardUrgency:
    def test_board_units_sorted_by_urgency(self, h):
        """Within each column, units must be sorted by due_date ascending
        (overdue first) with no-due-date units LAST."""
        board = requests.get(f"{API}/board", headers=h).json()
        for col in board["columns"]:
            dues = [u.get("due_date") for u in col["units"]]
            # Partition: non-null dues first, nulls last
            seen_null = False
            for d in dues:
                if d is None:
                    seen_null = True
                else:
                    assert not seen_null, f"column {col['status']} has unit with due_date after a null-due unit: {dues}"
            # Non-null portion sorted ascending (earliest/overdue first)
            non_null = [d for d in dues if d is not None]
            assert non_null == sorted(non_null), f"column {col['status']} not asc by due_date: {non_null}"

    def test_board_jobs_list_present(self, h):
        board = requests.get(f"{API}/board", headers=h).json()
        assert "jobs" in board and isinstance(board["jobs"], list)
        # Seeded job 26207 should be present (active)
        assert any(j["job_number"] == "26207" for j in board["jobs"])

    def test_board_filter_by_job(self, h):
        jobs = requests.get(f"{API}/jobs", headers=h).json()
        j = next(j for j in jobs if j["job_number"] == "26207")
        board = requests.get(f"{API}/board?job_id={j['id']}", headers=h).json()
        for col in board["columns"]:
            for u in col["units"]:
                assert u["job_id"] == j["id"]


class TestDigestCron:
    def test_cron_no_auth_401(self):
        r = requests.post(f"{API}/cron/digest", json={})
        assert r.status_code == 401

    def test_cron_wrong_bearer_401(self):
        r = requests.post(f"{API}/cron/digest", json={},
                          headers={"Authorization": "Bearer not-the-right-secret"})
        assert r.status_code == 401

    def test_preview_contains_morning_digest(self, h):
        r = requests.get(f"{API}/digest/preview", headers=h)
        assert r.status_code == 200
        d = r.json()
        assert "subject" in d and "html" in d
        assert "Morning Digest" in d["html"]

    def test_cron_queued_then_duplicate(self, h):
        """Call /api/cron/digest once with a unique X-Webhook-Id -> queued,
        same id again -> duplicate. NOTE: this will send ONE real email to
        the configured recipient (bmflorek@gmail.com) per test run."""
        secret = _load_env("WEBHOOK_CRON_SECRET")
        if not secret:
            pytest.skip("WEBHOOK_CRON_SECRET not set")
        run_id = f"regress-{uuid.uuid4().hex[:10]}"
        headers = {"Authorization": f"Bearer {secret}", "X-Webhook-Id": run_id}

        # Ensure recipients + enabled so we hit the 'queued' branch
        settings = requests.get(f"{API}/settings/digest", headers=h).json()
        recipients = settings.get("recipients") or []
        if not recipients:
            pytest.skip("No digest recipients configured; cannot verify 'queued' branch")

        r1 = requests.post(f"{API}/cron/digest", json={}, headers=headers)
        assert r1.status_code == 202, r1.text
        d1 = r1.json()
        assert d1["status"] in ("queued", "skipped"), d1
        assert d1["run_id"] == run_id

        # Same id -> duplicate
        r2 = requests.post(f"{API}/cron/digest", json={}, headers=headers)
        assert r2.status_code == 202
        d2 = r2.json()
        assert d2["status"] == "duplicate"
        assert d2["run_id"] == run_id


# ---------- Iteration 3: seed env credential sanity ----------
class TestSeedEnvLogin:
    def test_demo_credentials_from_env_work(self):
        """SEED_DEMO_EMAIL/SEED_DEMO_PASSWORD in backend/.env must match the
        actual seeded user."""
        env_email = _load_env("SEED_DEMO_EMAIL") or DEMO_EMAIL
        env_pass = _load_env("SEED_DEMO_PASSWORD") or DEMO_PASS
        r = requests.post(f"{API}/auth/login",
                          json={"email": env_email, "password": env_pass})
        assert r.status_code == 200, f"login failed with env creds {env_email}: {r.status_code} {r.text}"
