import uuid
from datetime import date
from database import execute_query, get_db_cursor
from services.audit_service import log_audit
from utils.helpers import paginate

def generate_asset_code() -> str:
    """Generates a clean unique asset code e.g. AST-2026-A1B2C3."""
    year = date.today().year
    code_suffix = uuid.uuid4().hex[:6].upper()
    candidate = f"AST-{year}-{code_suffix}"
    
    # Verify uniqueness in DB
    existing = execute_query("SELECT asset_id FROM assets WHERE asset_code = %s", (candidate,), fetch_one=True)
    if existing:
        return generate_asset_code()
    return candidate

def get_assets(search: str = None, status: str = None, category_id: int = None, page: int = 1, per_page: int = 10):
    """Retrieves paginated assets with search and filtering."""
    where_clauses = ["1=1"]
    params = []
    
    if search:
        search_term = f"%{search.strip()}%"
        where_clauses.append("(a.asset_name LIKE %s OR a.asset_code LIKE %s OR a.serial_number LIKE %s OR a.brand LIKE %s OR a.model_number LIKE %s)")
        params.extend([search_term, search_term, search_term, search_term, search_term])
        
    if status:
        where_clauses.append("a.asset_status = %s")
        params.append(status)
        
    if category_id:
        where_clauses.append("a.category_id = %s")
        params.append(category_id)
        
    where_sql = " AND ".join(where_clauses)
    
    # Total count
    count_sql = f"SELECT COUNT(*) AS total FROM assets a WHERE {where_sql}"
    count_row = execute_query(count_sql, tuple(params), fetch_one=True)
    total_items = count_row["total"] if count_row else 0
    
    pagination = paginate(total_items, page, per_page)
    
    # Data query
    data_sql = f"""
        SELECT 
            a.asset_id,
            a.asset_code,
            a.asset_name,
            a.category_id,
            a.vendor_id,
            a.brand,
            a.model_number,
            a.serial_number,
            a.purchase_date,
            a.purchase_cost,
            a.warranty_expiry,
            a.location,
            a.asset_status,
            a.created_at,
            c.category_name,
            v.vendor_name,
            e.full_name AS assigned_to_name,
            e.employee_code AS assigned_to_code
        FROM assets a
        LEFT JOIN asset_categories c ON a.category_id = c.category_id
        LEFT JOIN vendors v ON a.vendor_id = v.vendor_id
        LEFT JOIN asset_assignments aa ON a.asset_id = aa.asset_id AND aa.assignment_status = 'Assigned'
        LEFT JOIN employees e ON aa.employee_id = e.employee_id
        WHERE {where_sql}
        ORDER BY a.asset_id DESC
        LIMIT %s OFFSET %s
    """
    data_params = list(params) + [pagination["per_page"], pagination["offset"]]
    items = execute_query(data_sql, tuple(data_params), fetch_all=True)
    
    return items, pagination

def get_asset_by_id(asset_id: int):
    """Retrieves full details of a specific asset."""
    sql = """
        SELECT 
            a.*,
            c.category_name,
            v.vendor_name,
            v.contact_person AS vendor_contact,
            v.email AS vendor_email
        FROM assets a
        LEFT JOIN asset_categories c ON a.category_id = c.category_id
        LEFT JOIN vendors v ON a.vendor_id = v.vendor_id
        WHERE a.asset_id = %s
    """
    return execute_query(sql, (asset_id,), fetch_one=True)

def get_asset_assignment_history(asset_id: int):
    """Retrieves assignment history for an asset."""
    sql = """
        SELECT 
            aa.*,
            e.full_name AS employee_name,
            e.employee_code,
            d.department_name
        FROM asset_assignments aa
        JOIN employees e ON aa.employee_id = e.employee_id
        LEFT JOIN departments d ON e.department_id = d.department_id
        WHERE aa.asset_id = %s
        ORDER BY aa.assignment_id DESC
    """
    return execute_query(sql, (asset_id,), fetch_all=True)

def get_asset_maintenance_history(asset_id: int):
    """Retrieves maintenance records for an asset."""
    sql = """
        SELECT * FROM maintenance_records
        WHERE asset_id = %s
        ORDER BY maintenance_id DESC
    """
    return execute_query(sql, (asset_id,), fetch_all=True)

def create_asset(data: dict, user_id: int) -> int:
    """Creates a new asset and verifies constraints."""
    asset_code = data.get("asset_code", "").strip() or generate_asset_code()
    asset_name = data.get("asset_name", "").strip()
    category_id = data.get("category_id") or None
    vendor_id = data.get("vendor_id") or None
    brand = data.get("brand", "").strip() or None
    model_number = data.get("model_number", "").strip() or None
    serial_number = data.get("serial_number", "").strip() or None
    purchase_date = data.get("purchase_date") or None
    purchase_cost = data.get("purchase_cost") or None
    warranty_expiry = data.get("warranty_expiry") or None
    location = data.get("location", "").strip() or None
    asset_status = data.get("asset_status", "Available")
    
    if not asset_name:
        raise ValueError("Asset Name is required.")
        
    # Check duplicate asset code
    existing_code = execute_query("SELECT asset_id FROM assets WHERE asset_code = %s", (asset_code,), fetch_one=True)
    if existing_code:
        raise ValueError(f"Asset Code '{asset_code}' is already in use.")
        
    # Check duplicate serial number
    if serial_number:
        existing_serial = execute_query("SELECT asset_id FROM assets WHERE serial_number = %s", (serial_number,), fetch_one=True)
        if existing_serial:
            raise ValueError(f"Serial Number '{serial_number}' is already registered to another asset.")
            
    sql = """
        INSERT INTO assets (
            asset_code, asset_name, category_id, vendor_id, brand,
            model_number, serial_number, purchase_date, purchase_cost,
            warranty_expiry, location, asset_status, created_at
        ) VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, NOW()
        )
    """
    params = (
        asset_code, asset_name, category_id, vendor_id, brand,
        model_number, serial_number, purchase_date, purchase_cost,
        warranty_expiry, location, asset_status
    )
    new_id = execute_query(sql, params, commit=True, return_id=True)
    log_audit(user_id, "ASSET_CREATE", f"Created asset '{asset_name}' ({asset_code}) with ID {new_id}")
    return new_id

def update_asset(asset_id: int, data: dict, user_id: int):
    """Updates an existing asset with validation."""
    current = get_asset_by_id(asset_id)
    if not current:
        raise ValueError("Asset not found.")
        
    asset_name = data.get("asset_name", "").strip()
    if not asset_name:
        raise ValueError("Asset Name cannot be empty.")
        
    serial_number = data.get("serial_number", "").strip() or None
    if serial_number:
        existing_serial = execute_query(
            "SELECT asset_id FROM assets WHERE serial_number = %s AND asset_id != %s", 
            (serial_number, asset_id), 
            fetch_one=True
        )
        if existing_serial:
            raise ValueError(f"Serial Number '{serial_number}' is in use by another asset.")
            
    # Check if attempting to set status to 'Available' while actively assigned
    new_status = data.get("asset_status", current["asset_status"])
    if new_status == "Available":
        active_assignment = execute_query(
            "SELECT assignment_id FROM asset_assignments WHERE asset_id = %s AND assignment_status = 'Assigned'",
            (asset_id,),
            fetch_one=True
        )
        if active_assignment:
            raise ValueError("Cannot mark asset as 'Available' while it is actively assigned to an employee.")

    sql = """
        UPDATE assets SET
            asset_name = %s,
            category_id = %s,
            vendor_id = %s,
            brand = %s,
            model_number = %s,
            serial_number = %s,
            purchase_date = %s,
            purchase_cost = %s,
            warranty_expiry = %s,
            location = %s,
            asset_status = %s
        WHERE asset_id = %s
    """
    params = (
        asset_name,
        data.get("category_id") or None,
        data.get("vendor_id") or None,
        data.get("brand", "").strip() or None,
        data.get("model_number", "").strip() or None,
        serial_number,
        data.get("purchase_date") or None,
        data.get("purchase_cost") or None,
        data.get("warranty_expiry") or None,
        data.get("location", "").strip() or None,
        new_status,
        asset_id
    )
    execute_query(sql, params, commit=True)
    log_audit(user_id, "ASSET_UPDATE", f"Updated asset '{asset_name}' (ID: {asset_id})")

def delete_asset(asset_id: int, user_id: int):
    """Deletes an asset only if not actively assigned."""
    current = get_asset_by_id(asset_id)
    if not current:
        raise ValueError("Asset does not exist.")
        
    # Check active assignment
    active_assignment = execute_query(
        "SELECT assignment_id FROM asset_assignments WHERE asset_id = %s AND assignment_status = 'Assigned'",
        (asset_id,),
        fetch_one=True
    )
    if active_assignment:
        raise ValueError("Cannot delete this asset: it is currently assigned to an employee. Return the asset first.")
        
    # Check related maintenance records or historical assignments
    # Delete historical records or assignments safely if business rule permits, or handle cascade
    with get_db_cursor(commit=True) as (cursor, _):
        cursor.execute("DELETE FROM compliance_alerts WHERE asset_id = %s", (asset_id,))
        cursor.execute("DELETE FROM maintenance_records WHERE asset_id = %s", (asset_id,))
        cursor.execute("DELETE FROM asset_assignments WHERE asset_id = %s", (asset_id,))
        cursor.execute("DELETE FROM assets WHERE asset_id = %s", (asset_id,))
        
    log_audit(user_id, "ASSET_DELETE", f"Deleted asset '{current['asset_name']}' ({current['asset_code']})")

def assign_asset(asset_id: int, employee_id: int, remarks: str, user_id: int) -> int:
    """
    Performs atomic assignment of an asset to an active employee.
    Updates asset status to 'Assigned' and inserts into asset_assignments.
    """
    # 1. Verify asset exists and is Available
    asset = get_asset_by_id(asset_id)
    if not asset:
        raise ValueError("Asset not found.")
    if asset["asset_status"] != "Available":
        raise ValueError(f"Asset cannot be assigned because its current status is '{asset['asset_status']}'. Only 'Available' assets can be allocated.")
        
    # 2. Verify employee exists and is Active
    emp = execute_query("SELECT employee_id, full_name, employee_status FROM employees WHERE employee_id = %s", (employee_id,), fetch_one=True)
    if not emp:
        raise ValueError("Employee not found.")
    if emp["employee_status"] != "Active":
        raise ValueError(f"Cannot assign asset to inactive employee '{emp['full_name']}'.")
        
    # 3. Check for existing active assignment
    existing = execute_query(
        "SELECT assignment_id FROM asset_assignments WHERE asset_id = %s AND assignment_status = 'Assigned'",
        (asset_id,),
        fetch_one=True
    )
    if existing:
        raise ValueError("Asset already has an active assignment.")

    # 4. Atomic transaction
    with get_db_cursor(commit=True) as (cursor, _):
        insert_sql = """
            INSERT INTO asset_assignments (asset_id, employee_id, assigned_date, assignment_status, remarks)
            VALUES (%s, %s, CURDATE(), 'Assigned', %s)
        """
        cursor.execute(insert_sql, (asset_id, employee_id, remarks or None))
        assignment_id = cursor.lastrowid
        
        cursor.execute("UPDATE assets SET asset_status = 'Assigned' WHERE asset_id = %s", (asset_id,))
        
    log_audit(
        user_id, 
        "ASSET_ALLOCATE", 
        f"Assigned asset '{asset['asset_name']}' ({asset['asset_code']}) to employee '{emp['full_name']}' (Assignment ID: {assignment_id})"
    )
    return assignment_id

def return_asset(assignment_id: int, remarks: str, user_id: int):
    """
    Performs atomic return of an allocated asset.
    Updates return_date, assignment_status='Returned', and sets asset_status='Available'.
    """
    assignment = execute_query(
        """
        SELECT aa.*, a.asset_name, a.asset_code, e.full_name AS employee_name
        FROM asset_assignments aa
        JOIN assets a ON aa.asset_id = a.asset_id
        JOIN employees e ON aa.employee_id = e.employee_id
        WHERE aa.assignment_id = %s
        """,
        (assignment_id,),
        fetch_one=True
    )
    if not assignment:
        raise ValueError("Assignment record not found.")
    if assignment["assignment_status"] == "Returned":
        raise ValueError("Asset is already marked as returned.")
        
    combined_remarks = assignment["remarks"] or ""
    if remarks:
        combined_remarks = f"{combined_remarks} | Return Note: {remarks}".strip(" |")

    with get_db_cursor(commit=True) as (cursor, _):
        cursor.execute(
            """
            UPDATE asset_assignments 
            SET return_date = CURDATE(), assignment_status = 'Returned', remarks = %s
            WHERE assignment_id = %s
            """,
            (combined_remarks, assignment_id)
        )
        cursor.execute(
            "UPDATE assets SET asset_status = 'Available' WHERE asset_id = %s",
            (assignment["asset_id"],)
        )
        
    log_audit(
        user_id,
        "ASSET_RETURN",
        f"Returned asset '{assignment['asset_name']}' ({assignment['asset_code']}) from employee '{assignment['employee_name']}'"
    )

def get_assignments(search: str = None, status: str = None, page: int = 1, per_page: int = 10):
    """Retrieves paginated asset assignments with search and status filtering."""
    where_clauses = ["1=1"]
    params = []
    
    if search:
        search_term = f"%{search.strip()}%"
        where_clauses.append("(a.asset_name LIKE %s OR a.asset_code LIKE %s OR e.full_name LIKE %s OR e.employee_code LIKE %s)")
        params.extend([search_term, search_term, search_term, search_term])
        
    if status:
        where_clauses.append("aa.assignment_status = %s")
        params.append(status)
        
    where_sql = " AND ".join(where_clauses)
    
    count_sql = f"""
        SELECT COUNT(*) AS total 
        FROM asset_assignments aa
        JOIN assets a ON aa.asset_id = a.asset_id
        JOIN employees e ON aa.employee_id = e.employee_id
        WHERE {where_sql}
    """
    count_row = execute_query(count_sql, tuple(params), fetch_one=True)
    total_items = count_row["total"] if count_row else 0
    
    pagination = paginate(total_items, page, per_page)
    
    data_sql = f"""
        SELECT 
            aa.assignment_id,
            aa.asset_id,
            aa.employee_id,
            aa.assigned_date,
            aa.return_date,
            aa.assignment_status,
            aa.remarks,
            a.asset_name,
            a.asset_code,
            a.serial_number,
            e.full_name AS employee_name,
            e.employee_code,
            d.department_name
        FROM asset_assignments aa
        JOIN assets a ON aa.asset_id = a.asset_id
        JOIN employees e ON aa.employee_id = e.employee_id
        LEFT JOIN departments d ON e.department_id = d.department_id
        WHERE {where_sql}
        ORDER BY aa.assignment_id DESC
        LIMIT %s OFFSET %s
    """
    data_params = list(params) + [pagination["per_page"], pagination["offset"]]
    items = execute_query(data_sql, tuple(data_params), fetch_all=True)
    return items, pagination
