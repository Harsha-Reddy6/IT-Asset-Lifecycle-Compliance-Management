import pytest
from app import create_app
from config import TestConfig
from database import check_db_health, execute_query

@pytest.fixture(scope="session")
def app():
    test_app = create_app(TestConfig)
    test_app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret-key"
    })
    return test_app

@pytest.fixture(scope="session")
def db_available():
    return check_db_health()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def admin_client(app):
    client = app.test_client()
    with client.session_transaction() as sess:
        # Fetch actual admin user from MySQL
        admin_user = execute_query("SELECT id, username, full_name, email, role FROM users WHERE username = 'admin'", fetch_one=True)
        if admin_user:
            sess["user_id"] = admin_user["id"]
            sess["username"] = admin_user["username"]
            sess["full_name"] = admin_user["full_name"]
            sess["email"] = admin_user["email"]
            sess["role"] = "admin"
        else:
            sess["user_id"] = 1
            sess["username"] = "admin"
            sess["full_name"] = "Administrator"
            sess["email"] = "admin@test.com"
            sess["role"] = "admin"
    return client

@pytest.fixture
def employee_client(app):
    client = app.test_client()
    with client.session_transaction() as sess:
        emp_user = execute_query("SELECT id, username, full_name, email, role FROM users WHERE role = 'employee' LIMIT 1", fetch_one=True)
        if emp_user:
            sess["user_id"] = emp_user["id"]
            sess["username"] = emp_user["username"]
            sess["full_name"] = emp_user["full_name"]
            sess["email"] = emp_user["email"]
            sess["role"] = "employee"
            
            emp = execute_query("SELECT employee_id FROM employees WHERE user_id = %s", (emp_user["id"],), fetch_one=True)
            sess["employee_id"] = emp["employee_id"] if emp else None
        else:
            sess["user_id"] = 99
            sess["username"] = "testemp"
            sess["full_name"] = "Test Employee"
            sess["email"] = "emp@test.com"
            sess["role"] = "employee"
    return client
