import uuid
from database import execute_query

def test_employee_crud_and_validation(admin_client):
    """Test 7: Employee CRUD workflows, uniqueness and validations."""
    suffix = uuid.uuid4().hex[:6]
    emp_code = f"EMP-TEST-{suffix.upper()}"
    emp_email = f"emp_{suffix}@testorg.com"
    emp_name = f"Test Integration Emp {suffix}"
    
    # 1. Add Employee
    res_add = admin_client.post("/employees/add", data={
        "full_name": emp_name,
        "email": emp_email,
        "employee_code": emp_code,
        "department_id": 1,
        "designation": "QA Automation Engineer",
        "joining_date": "2024-06-01",
        "employee_status": "Active"
    }, follow_redirects=True)
    assert res_add.status_code == 200
    assert b"added successfully" in res_add.data
    
    emp = execute_query("SELECT * FROM employees WHERE employee_code = %s", (emp_code,), fetch_one=True)
    assert emp is not None
    assert emp["full_name"] == emp_name
    emp_id = emp["employee_id"]

    # 2. Duplicate code / email rejection
    res_dup = admin_client.post("/employees/add", data={
        "full_name": "Clone Person",
        "email": emp_email,  # duplicate email!
        "employee_code": f"EMP-NEW-{suffix}",
        "employee_status": "Active"
    }, follow_redirects=True)
    assert b"already registered" in res_dup.data

    # 3. Edit Employee
    res_edit = admin_client.post(f"/employees/edit/{emp_id}", data={
        "full_name": f"Updated {emp_name}",
        "email": emp_email,
        "department_id": 1,
        "designation": "Lead Automation Engineer",
        "employee_status": "Active"
    }, follow_redirects=True)
    assert res_edit.status_code == 200
    assert b"updated successfully" in res_edit.data

    # 4. Delete Employee
    res_del = admin_client.post(f"/employees/delete/{emp_id}", follow_redirects=True)
    assert res_del.status_code == 200
    assert b"deleted successfully" in res_del.data

    deleted = execute_query("SELECT employee_id FROM employees WHERE employee_id = %s", (emp_id,), fetch_one=True)
    assert deleted is None

def test_department_crud(admin_client):
    """Test 8: Department CRUD workflow."""
    suffix = uuid.uuid4().hex[:6]
    dept_name = f"Test Department {suffix}"
    
    # Add
    res = admin_client.post("/departments/add", data={
        "department_name": dept_name,
        "description": "Department for automated tests"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"created successfully" in res.data
    
    dept = execute_query("SELECT * FROM departments WHERE department_name = %s", (dept_name,), fetch_one=True)
    assert dept is not None
    dept_id = dept["department_id"]

    # Edit
    res_edit = admin_client.post(f"/departments/edit/{dept_id}", data={
        "department_name": f"{dept_name} Updated",
        "description": "Updated description"
    }, follow_redirects=True)
    assert b"updated successfully" in res_edit.data

    # Delete
    res_del = admin_client.post(f"/departments/delete/{dept_id}", follow_redirects=True)
    assert b"deleted" in res_del.data
