import uuid
from database import execute_query
from services.compliance_service import run_compliance_scan

def test_license_lifecycle_and_allocation(admin_client):
    """Test 12, 13 & 14: License creation, allocation limit checks, and revocation."""
    suffix = uuid.uuid4().hex[:6].upper()
    lic_key = f"TEST-LIC-{suffix}"
    
    # 1. Create a 1-seat license
    res_create = admin_client.post("/licenses/add", data={
        "software_id": 1,
        "vendor_id": 1,
        "license_key": lic_key,
        "total_licenses": 1,
        "purchase_date": "2024-01-01",
        "expiry_date": "2027-01-01",
        "license_cost": "500.00",
        "license_status": "Active"
    }, follow_redirects=True)
    assert res_create.status_code == 200
    assert b"created successfully" in res_create.data
    
    lic = execute_query("SELECT * FROM software_licenses WHERE license_key = %s", (lic_key,), fetch_one=True)
    assert lic is not None
    lic_id = lic["license_id"]

    # Select two active employees
    employees = execute_query("SELECT employee_id FROM employees WHERE employee_status = 'Active' LIMIT 2", fetch_all=True)
    assert len(employees) >= 2
    emp1_id = employees[0]["employee_id"]
    emp2_id = employees[1]["employee_id"]

    # 2. Allocate the single seat to emp1
    res_assign1 = admin_client.post("/license-assignments/add", data={
        "license_id": lic_id,
        "employee_id": emp1_id
    }, follow_redirects=True)
    assert res_assign1.status_code == 200
    assert b"allocated successfully" in res_assign1.data

    # 3. Duplicate allocation to same employee prevention
    res_dup = admin_client.post("/license-assignments/add", data={
        "license_id": lic_id,
        "employee_id": emp1_id
    }, follow_redirects=True)
    assert b"already holds an active seat" in res_dup.data or b"assigned" in res_dup.data

    # 4. Over-allocation prevention: allocate beyond total_licenses (capacity is 1, already 1 used)
    res_over = admin_client.post("/license-assignments/add", data={
        "license_id": lic_id,
        "employee_id": emp2_id
    }, follow_redirects=True)
    assert b"already assigned" in res_over.data or b"available" in res_over.data

    # 5. Revoke the license seat
    assign_row = execute_query(
        "SELECT license_assignment_id FROM license_assignments WHERE license_id = %s AND employee_id = %s AND assignment_status = 'Assigned'",
        (lic_id, emp1_id),
        fetch_one=True
    )
    assert assign_row is not None
    assign_id = assign_row["license_assignment_id"]

    res_return = admin_client.post(f"/license-assignments/return/{assign_id}", follow_redirects=True)
    assert res_return.status_code == 200
    assert b"returned and available" in res_return.data

    # 6. Now emp2 CAN be allocated the seat!
    res_assign2 = admin_client.post("/license-assignments/add", data={
        "license_id": lic_id,
        "employee_id": emp2_id
    }, follow_redirects=True)
    assert res_assign2.status_code == 200
    assert b"allocated successfully" in res_assign2.data

    # Cleanup
    execute_query("DELETE FROM license_assignments WHERE license_id = %s", (lic_id,), commit=True)
    execute_query("DELETE FROM software_licenses WHERE license_id = %s", (lic_id,), commit=True)

def test_compliance_and_scan(admin_client):
    """Test 16: Automated compliance scan and alert resolution."""
    # Run scan
    res_scan = admin_client.post("/compliance", follow_redirects=True)
    assert res_scan.status_code == 200
    assert b"Compliance scan completed" in res_scan.data

    # Fetch an open alert to resolve
    open_alert = execute_query("SELECT alert_id FROM compliance_alerts WHERE alert_status = 'Open' LIMIT 1", fetch_one=True)
    if open_alert:
        al_id = open_alert["alert_id"]
        res_resolve = admin_client.post(f"/compliance/resolve/{al_id}", follow_redirects=True)
        assert res_resolve.status_code == 200
        assert b"marked as Resolved" in res_resolve.data

def test_reports_and_csv_exports(admin_client):
    """Test 18: Reporting hub and CSV data exports."""
    # 1. Reports hub
    res_hub = admin_client.get("/reports")
    assert res_hub.status_code == 200
    assert b"Hardware Inventory Report" in res_hub.data

    # 2. Asset CSV Export
    res_asset_csv = admin_client.get("/reports/export?type=assets")
    assert res_asset_csv.status_code == 200
    assert res_asset_csv.mimetype == "text/csv"
    assert b"Asset Code" in res_asset_csv.data

    # 3. License CSV Export
    res_lic_csv = admin_client.get("/reports/export?type=licenses")
    assert res_lic_csv.status_code == 200
    assert res_lic_csv.mimetype == "text/csv"
    assert b"Software Name" in res_lic_csv.data
