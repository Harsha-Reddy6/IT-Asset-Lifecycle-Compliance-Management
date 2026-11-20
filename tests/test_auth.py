import uuid
from database import check_db_health, execute_query

def test_startup_and_health(client, db_available):
    """Test 1 & 2: Application startup and MySQL connection."""
    assert db_available is True
    res = client.get("/")
    assert res.status_code in [302, 200]

def test_protected_pages_unauthenticated(client):
    """Test 5: Protected pages redirect unauthenticated users to login."""
    endpoints = ["/dashboard", "/employees", "/assets", "/licenses", "/compliance", "/reports", "/profile"]
    for ep in endpoints:
        res = client.get(ep, follow_redirects=False)
        assert res.status_code == 302
        assert "/login" in res.headers["Location"]

def test_user_registration_and_validation(client):
    """Test 3: User registration workflow and duplicate prevention."""
    unique_suffix = uuid.uuid4().hex[:6]
    test_username = f"user_{unique_suffix}"
    test_email = f"user_{unique_suffix}@company.com"
    
    # 1. Successful employee registration
    res = client.post("/register", data={
        "full_name": "New Test Employee",
        "email": test_email,
        "username": test_username,
        "password": "Password@123",
        "confirm_password": "Password@123"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Registration successful" in res.data or b"Sign In" in res.data
    
    # Verify user in database
    user = execute_query("SELECT id, role, email FROM users WHERE username = %s", (test_username,), fetch_one=True)
    assert user is not None
    assert user["role"] == "employee"  # Must NOT be admin!
    
    # 2. Duplicate registration attempt
    dup_res = client.post("/register", data={
        "full_name": "Duplicate User",
        "email": test_email,
        "username": test_username,
        "password": "Password@123",
        "confirm_password": "Password@123"
    }, follow_redirects=True)
    assert b"already exists" in dup_res.data

    # 3. Password mismatch validation
    mismatch_res = client.post("/register", data={
        "full_name": "Mismatch User",
        "email": f"mismatch_{unique_suffix}@company.com",
        "username": f"mismatch_{unique_suffix}",
        "password": "Password@123",
        "confirm_password": "DifferentPassword@123"
    }, follow_redirects=True)
    assert b"Passwords do not match" in mismatch_res.data

def test_login_and_logout(client):
    """Test 4: Login with valid/invalid credentials and logout."""
    # Invalid login
    res_bad = client.post("/login", data={
        "identifier": "admin",
        "password": "wrong_password_xyz"
    }, follow_redirects=True)
    assert b"Invalid credentials" in res_bad.data

    # Valid login with admin
    res_good = client.post("/login", data={
        "identifier": "admin",
        "password": "Admin@123"
    }, follow_redirects=True)
    assert res_good.status_code == 200
    assert b"Welcome back" in res_good.data or b"Dashboard" in res_good.data

    # Logout
    res_logout = client.get("/logout", follow_redirects=True)
    assert res_logout.status_code == 200
    assert b"logged out" in res_logout.data

def test_role_based_permissions(employee_client):
    """Test 6: Enforce admin vs employee permissions."""
    # Employee attempting admin-only routes
    res = employee_client.get("/employees/add", follow_redirects=True)
    assert res.status_code == 200
    assert b"Access denied" in res.data or b"Administrator privileges" in res.data

    res_post = employee_client.post("/employees/delete/1", follow_redirects=True)
    assert b"Access denied" in res_post.data or b"Administrator privileges" in res_post.data

def test_all_pages_render_for_admin(admin_client):
    """Test 20: Comprehensive check that all main view routes render 200 OK for logged-in admin."""
    routes = [
        "/dashboard",
        "/employees",
        "/departments",
        "/assets",
        "/categories",
        "/assignments",
        "/vendors",
        "/software",
        "/licenses",
        "/license-assignments",
        "/maintenance",
        "/purchase-orders",
        "/compliance",
        "/reports",
        "/reports/assets",
        "/reports/licenses",
        "/reports/compliance",
        "/profile"
    ]
    for r in routes:
        res = admin_client.get(r)
        assert res.status_code == 200, f"Route {r} returned status {res.status_code}"

