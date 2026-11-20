import uuid
from database import execute_query
from services.asset_service import create_asset, delete_asset

def test_asset_assignment_and_return_lifecycle(admin_client):
    """Test 10 & 11: Complete asset allocation, transaction integrity, and return lifecycle."""
    suffix = uuid.uuid4().hex[:6].upper()
    serial_num = f"SN-ASSIGN-{suffix}"
    
    # 1. Create an available asset
    asset_id = create_asset({
        "asset_name": f"Assignment Test Laptop {suffix}",
        "serial_number": serial_num,
        "asset_status": "Available"
    }, user_id=1)
    
    # Select active employee
    emp = execute_query("SELECT employee_id FROM employees WHERE employee_status = 'Active' LIMIT 1", fetch_one=True)
    assert emp is not None
    emp_id = emp["employee_id"]

    # 2. Allocate Asset
    assign_res = admin_client.post("/assignments/add", data={
        "asset_id": asset_id,
        "employee_id": emp_id,
        "remarks": "Assigned for functional testing"
    }, follow_redirects=True)
    assert assign_res.status_code == 200
    assert b"allocated successfully" in assign_res.data

    # Verify atomic update
    asset_after = execute_query("SELECT asset_status FROM assets WHERE asset_id = %s", (asset_id,), fetch_one=True)
    assert asset_after["asset_status"] == "Assigned"

    assignment = execute_query(
        "SELECT * FROM asset_assignments WHERE asset_id = %s AND assignment_status = 'Assigned'",
        (asset_id,),
        fetch_one=True
    )
    assert assignment is not None
    assignment_id = assignment["assignment_id"]

    # 3. Attempt to delete actively assigned asset (must fail!)
    del_blocked = admin_client.post(f"/assets/delete/{asset_id}", follow_redirects=True)
    assert b"currently assigned" in del_blocked.data
    
    # 4. Attempt to assign already assigned asset (must fail!)
    reassign_res = admin_client.post("/assignments/add", data={
        "asset_id": asset_id,
        "employee_id": emp_id
    }, follow_redirects=True)
    assert b"Only 'Available' assets can be allocated" in reassign_res.data or b"cannot be assigned" in reassign_res.data

    # 5. Return the asset
    return_res = admin_client.post(f"/assignments/return/{assignment_id}", data={
        "remarks": "Returned in perfect condition"
    }, follow_redirects=True)
    assert return_res.status_code == 200
    assert b"returned successfully" in return_res.data

    # Verify status changed back to Available
    asset_final = execute_query("SELECT asset_status FROM assets WHERE asset_id = %s", (asset_id,), fetch_one=True)
    assert asset_final["asset_status"] == "Available"

    # Cleanup asset
    delete_asset(asset_id, user_id=1)

def test_maintenance_status_updates(admin_client):
    """Test 15: Maintenance workflow and asset status coordination."""
    suffix = uuid.uuid4().hex[:6].upper()
    asset_id = create_asset({
        "asset_name": f"Maintenance Test Device {suffix}",
        "serial_number": f"SN-MAINT-{suffix}",
        "asset_status": "Available"
    }, user_id=1)

    # 1. Log Pending Maintenance -> Asset should become 'Under Maintenance'
    res_maint = admin_client.post("/maintenance/add", data={
        "asset_id": asset_id,
        "maintenance_type": "Battery Replacement",
        "maintenance_date": "2024-11-01",
        "cost": "150.00",
        "description": "Routine battery swap",
        "maintenance_status": "In Progress"
    }, follow_redirects=True)
    assert res_maint.status_code == 200
    assert b"created successfully" in res_maint.data

    asset_maint = execute_query("SELECT asset_status FROM assets WHERE asset_id = %s", (asset_id,), fetch_one=True)
    assert asset_maint["asset_status"] == "Under Maintenance"

    maint_row = execute_query("SELECT maintenance_id FROM maintenance_records WHERE asset_id = %s", (asset_id,), fetch_one=True)
    m_id = maint_row["maintenance_id"]

    # 2. Mark Completed -> Asset should become 'Available'
    res_complete = admin_client.post(f"/maintenance/edit/{m_id}", data={
        "maintenance_type": "Battery Replacement",
        "maintenance_date": "2024-11-02",
        "cost": "150.00",
        "maintenance_status": "Completed"
    }, follow_redirects=True)
    assert res_complete.status_code == 200
    assert b"updated successfully" in res_complete.data

    asset_done = execute_query("SELECT asset_status FROM assets WHERE asset_id = %s", (asset_id,), fetch_one=True)
    assert asset_done["asset_status"] == "Available"

    # Cleanup
    delete_asset(asset_id, user_id=1)
