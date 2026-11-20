import uuid
from database import execute_query

def test_asset_crud_and_validation(admin_client):
    """Test 9: Asset CRUD operations, uniqueness constraints, and search."""
    unique_suffix = uuid.uuid4().hex[:6].upper()
    serial_num = f"SN-TEST-{unique_suffix}"
    asset_name = f"Test Workstation {unique_suffix}"
    
    # 1. Create Asset
    create_res = admin_client.post("/assets/add", data={
        "asset_name": asset_name,
        "asset_code": "",  # test auto-generation
        "category_id": 1,
        "vendor_id": 1,
        "brand": "Dell",
        "model_number": "Precision-5570",
        "serial_number": serial_num,
        "purchase_date": "2024-05-01",
        "purchase_cost": "2499.50",
        "warranty_expiry": "2027-05-01",
        "location": "Lab 4",
        "asset_status": "Available"
    }, follow_redirects=True)
    assert create_res.status_code == 200
    assert b"added successfully" in create_res.data
    
    # Verify in DB
    created = execute_query("SELECT * FROM assets WHERE serial_number = %s", (serial_num,), fetch_one=True)
    assert created is not None
    assert created["asset_name"] == asset_name
    assert created["asset_code"].startswith("AST-")
    asset_id = created["asset_id"]

    # 2. Duplicate serial number prevention
    dup_res = admin_client.post("/assets/add", data={
        "asset_name": "Another Laptop",
        "asset_code": f"AST-DUP-{unique_suffix}",
        "serial_number": serial_num,  # duplicate!
        "asset_status": "Available"
    }, follow_redirects=True)
    assert b"already registered" in dup_res.data

    # 3. View Asset Details
    view_res = admin_client.get(f"/assets/view/{asset_id}")
    assert view_res.status_code == 200
    assert asset_name.encode() in view_res.data

    # 4. Edit Asset
    updated_name = f"Updated {asset_name}"
    edit_res = admin_client.post(f"/assets/edit/{asset_id}", data={
        "asset_name": updated_name,
        "category_id": 1,
        "brand": "Dell",
        "model_number": "Precision-5570",
        "serial_number": serial_num,
        "purchase_cost": "2600.00",
        "location": "Lab 5",
        "asset_status": "Available"
    }, follow_redirects=True)
    assert edit_res.status_code == 200
    assert b"updated successfully" in edit_res.data
    
    # 5. Delete Asset
    del_res = admin_client.post(f"/assets/delete/{asset_id}", follow_redirects=True)
    assert del_res.status_code == 200
    assert b"deleted successfully" in del_res.data
    
    # Confirm deletion from DB
    deleted = execute_query("SELECT asset_id FROM assets WHERE asset_id = %s", (asset_id,), fetch_one=True)
    assert deleted is None

def test_asset_filters_and_search(admin_client):
    """Test 19: Search and filter on assets list."""
    res = admin_client.get("/assets?search=Dell&status=Assigned", follow_redirects=True)
    assert res.status_code == 200
    assert b"Asset Code" in res.data
