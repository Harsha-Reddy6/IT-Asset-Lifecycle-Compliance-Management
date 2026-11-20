from datetime import date
from database import execute_query, get_db_cursor
from services.audit_service import log_audit
from utils.helpers import paginate

def get_licenses(search: str = None, status: str = None, page: int = 1, per_page: int = 10):
    """Retrieves software licenses with dynamic seat utilization calculation."""
    where_clauses = ["1=1"]
    params = []
    
    if search:
        search_term = f"%{search.strip()}%"
        where_clauses.append("(s.software_name LIKE %s OR s.publisher LIKE %s OR sl.license_key LIKE %s)")
        params.extend([search_term, search_term, search_term])
        
    if status:
        where_clauses.append("sl.license_status = %s")
        params.append(status)
        
    where_sql = " AND ".join(where_clauses)
    
    count_sql = f"""
        SELECT COUNT(*) AS total 
        FROM software_licenses sl
        JOIN software s ON sl.software_id = s.software_id
        WHERE {where_sql}
    """
    count_row = execute_query(count_sql, tuple(params), fetch_one=True)
    total_items = count_row["total"] if count_row else 0
    
    pagination = paginate(total_items, page, per_page)
    
    data_sql = f"""
        SELECT 
            sl.license_id,
            sl.software_id,
            sl.vendor_id,
            sl.license_key,
            sl.total_licenses,
            sl.purchase_date,
            sl.expiry_date,
            sl.license_cost,
            sl.license_status,
            s.software_name,
            s.publisher,
            s.software_category,
            s.version,
            v.vendor_name,
            COUNT(CASE WHEN la.assignment_status = 'Assigned' THEN 1 END) AS assigned_count,
            (sl.total_licenses - COUNT(CASE WHEN la.assignment_status = 'Assigned' THEN 1 END)) AS available_count
        FROM software_licenses sl
        JOIN software s ON sl.software_id = s.software_id
        LEFT JOIN vendors v ON sl.vendor_id = v.vendor_id
        LEFT JOIN license_assignments la ON sl.license_id = la.license_id
        WHERE {where_sql}
        GROUP BY sl.license_id, sl.software_id, sl.vendor_id, sl.license_key, 
                 sl.total_licenses, sl.purchase_date, sl.expiry_date, sl.license_cost, 
                 sl.license_status, s.software_name, s.publisher, s.software_category, 
                 s.version, v.vendor_name
        ORDER BY sl.license_id DESC
        LIMIT %s OFFSET %s
    """
    data_params = list(params) + [pagination["per_page"], pagination["offset"]]
    items = execute_query(data_sql, tuple(data_params), fetch_all=True)
    return items, pagination

def get_license_by_id(license_id: int):
    """Retrieves full details of a specific license including seat counts."""
    sql = """
        SELECT 
            sl.*,
            s.software_name,
            s.publisher,
            s.version,
            s.software_category,
            v.vendor_name,
            COUNT(CASE WHEN la.assignment_status = 'Assigned' THEN 1 END) AS assigned_count,
            (sl.total_licenses - COUNT(CASE WHEN la.assignment_status = 'Assigned' THEN 1 END)) AS available_count
        FROM software_licenses sl
        JOIN software s ON sl.software_id = s.software_id
        LEFT JOIN vendors v ON sl.vendor_id = v.vendor_id
        LEFT JOIN license_assignments la ON sl.license_id = la.license_id
        WHERE sl.license_id = %s
        GROUP BY sl.license_id, sl.software_id, sl.vendor_id, sl.license_key, 
                 sl.total_licenses, sl.purchase_date, sl.expiry_date, sl.license_cost, 
                 sl.license_status, s.software_name, s.publisher, s.version, 
                 s.software_category, v.vendor_name
    """
    return execute_query(sql, (license_id,), fetch_one=True)

def create_license(data: dict, user_id: int) -> int:
    """Creates a new software license record."""
    software_id = data.get("software_id")
    if not software_id:
        raise ValueError("Please select software for the license.")
        
    total_licenses = int(data.get("total_licenses", 1))
    if total_licenses <= 0:
        raise ValueError("Total licenses must be at least 1.")
        
    sql = """
        INSERT INTO software_licenses (
            software_id, vendor_id, license_key, total_licenses,
            purchase_date, expiry_date, license_cost, license_status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        software_id,
        data.get("vendor_id") or None,
        data.get("license_key", "").strip() or None,
        total_licenses,
        data.get("purchase_date") or None,
        data.get("expiry_date") or None,
        data.get("license_cost") or None,
        data.get("license_status", "Active")
    )
    new_id = execute_query(sql, params, commit=True, return_id=True)
    log_audit(user_id, "LICENSE_CREATE", f"Created license ID {new_id} for software ID {software_id} with {total_licenses} seats")
    return new_id

def update_license(license_id: int, data: dict, user_id: int):
    """Updates an existing software license record."""
    current = get_license_by_id(license_id)
    if not current:
        raise ValueError("Software license record not found.")
        
    total_licenses = int(data.get("total_licenses", current["total_licenses"]))
    if total_licenses < current["assigned_count"]:
        raise ValueError(
            f"Cannot reduce total licenses to {total_licenses}. Currently {current['assigned_count']} seats are actively assigned."
        )
        
    sql = """
        UPDATE software_licenses SET
            software_id = %s,
            vendor_id = %s,
            license_key = %s,
            total_licenses = %s,
            purchase_date = %s,
            expiry_date = %s,
            license_cost = %s,
            license_status = %s
        WHERE license_id = %s
    """
    params = (
        data.get("software_id", current["software_id"]),
        data.get("vendor_id") or None,
        data.get("license_key", "").strip() or None,
        total_licenses,
        data.get("purchase_date") or None,
        data.get("expiry_date") or None,
        data.get("license_cost") or None,
        data.get("license_status", current["license_status"]),
        license_id
    )
    execute_query(sql, params, commit=True)
    log_audit(user_id, "LICENSE_UPDATE", f"Updated license ID {license_id} ({current['software_name']})")

def assign_license(license_id: int, employee_id: int, user_id: int) -> int:
    """
    Assigns an available license seat to an employee.
    Enforces capacity limits and prevents duplicate active assignments.
    """
    license_info = get_license_by_id(license_id)
    if not license_info:
        raise ValueError("Software license not found.")
        
    if license_info["license_status"] != "Active":
        raise ValueError(f"Cannot allocate seat: License status is '{license_info['license_status']}'. Only 'Active' licenses can be assigned.")
        
    # Expiry check
    if license_info["expiry_date"] and license_info["expiry_date"] < date.today():
        raise ValueError("Cannot assign seat: This software license has expired.")
        
    # Capacity check
    if license_info["available_count"] <= 0:
        raise ValueError(f"All {license_info['total_licenses']} seats for '{license_info['software_name']}' are already assigned.")
        
    # Employee check
    emp = execute_query(
        "SELECT employee_id, full_name, employee_status FROM employees WHERE employee_id = %s",
        (employee_id,),
        fetch_one=True
    )
    if not emp:
        raise ValueError("Selected employee not found.")
    if emp["employee_status"] != "Active":
        raise ValueError(f"Cannot assign license to inactive employee '{emp['full_name']}'.")
        
    # Duplicate active assignment check
    existing = execute_query(
        """
        SELECT license_assignment_id FROM license_assignments 
        WHERE license_id = %s AND employee_id = %s AND assignment_status = 'Assigned'
        """,
        (license_id, employee_id),
        fetch_one=True
    )
    if existing:
        raise ValueError(f"Employee '{emp['full_name']}' already holds an active seat for this license.")
        
    sql = """
        INSERT INTO license_assignments (license_id, employee_id, assigned_date, assignment_status)
        VALUES (%s, %s, CURDATE(), 'Assigned')
    """
    assignment_id = execute_query(sql, (license_id, employee_id), commit=True, return_id=True)
    log_audit(
        user_id,
        "LICENSE_ALLOCATE",
        f"Allocated seat of '{license_info['software_name']}' to employee '{emp['full_name']}' (Assignment ID: {assignment_id})"
    )
    return assignment_id

def return_license(assignment_id: int, user_id: int):
    """Marks a software license seat assignment as returned."""
    assignment = execute_query(
        """
        SELECT la.*, s.software_name, e.full_name AS employee_name
        FROM license_assignments la
        JOIN software_licenses sl ON la.license_id = sl.license_id
        JOIN software s ON sl.software_id = s.software_id
        JOIN employees e ON la.employee_id = e.employee_id
        WHERE la.license_assignment_id = %s
        """,
        (assignment_id,),
        fetch_one=True
    )
    if not assignment:
        raise ValueError("License assignment record not found.")
    if assignment["assignment_status"] == "Returned":
        raise ValueError("License seat is already returned.")
        
    sql = """
        UPDATE license_assignments 
        SET return_date = CURDATE(), assignment_status = 'Returned'
        WHERE license_assignment_id = %s
    """
    execute_query(sql, (assignment_id,), commit=True)
    log_audit(
        user_id,
        "LICENSE_RETURN",
        f"Revoked seat of '{assignment['software_name']}' from employee '{assignment['employee_name']}'"
    )

def get_license_assignments(license_id: int = None, search: str = None, status: str = None, page: int = 1, per_page: int = 10):
    """Retrieves paginated license seat allocations."""
    where_clauses = ["1=1"]
    params = []
    
    if license_id:
        where_clauses.append("la.license_id = %s")
        params.append(license_id)
        
    if search:
        search_term = f"%{search.strip()}%"
        where_clauses.append("(s.software_name LIKE %s OR e.full_name LIKE %s OR e.employee_code LIKE %s)")
        params.extend([search_term, search_term, search_term])
        
    if status:
        where_clauses.append("la.assignment_status = %s")
        params.append(status)
        
    where_sql = " AND ".join(where_clauses)
    
    count_sql = f"""
        SELECT COUNT(*) AS total
        FROM license_assignments la
        JOIN software_licenses sl ON la.license_id = sl.license_id
        JOIN software s ON sl.software_id = s.software_id
        JOIN employees e ON la.employee_id = e.employee_id
        WHERE {where_sql}
    """
    count_row = execute_query(count_sql, tuple(params), fetch_one=True)
    total_items = count_row["total"] if count_row else 0
    
    pagination = paginate(total_items, page, per_page)
    
    data_sql = f"""
        SELECT 
            la.license_assignment_id,
            la.license_id,
            la.employee_id,
            la.assigned_date,
            la.return_date,
            la.assignment_status,
            s.software_name,
            s.version,
            sl.license_key,
            e.full_name AS employee_name,
            e.employee_code,
            e.email AS employee_email,
            d.department_name
        FROM license_assignments la
        JOIN software_licenses sl ON la.license_id = sl.license_id
        JOIN software s ON sl.software_id = s.software_id
        JOIN employees e ON la.employee_id = e.employee_id
        LEFT JOIN departments d ON e.department_id = d.department_id
        WHERE {where_sql}
        ORDER BY la.license_assignment_id DESC
        LIMIT %s OFFSET %s
    """
    data_params = list(params) + [pagination["per_page"], pagination["offset"]]
    items = execute_query(data_sql, tuple(data_params), fetch_all=True)
    return items, pagination
