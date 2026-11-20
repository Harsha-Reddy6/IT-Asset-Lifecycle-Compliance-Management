import sys
from database import execute_query
from utils.auth import hash_password

def setup_admin(username="admin", email="admin@organization.com", password="Admin@123", full_name="System Administrator"):
    """
    Creates or updates the initial Administrator account.
    """
    print(f"Creating / Updating Admin User: {username} ({email})...")
    
    existing = execute_query("SELECT id FROM users WHERE username = %s OR email = %s", (username, email), fetch_one=True)
    pw_hash = hash_password(password)
    
    if existing:
        user_id = existing["id"]
        execute_query("""
            UPDATE users 
            SET full_name = %s, email = %s, username = %s, password_hash = %s, role = 'admin'
            WHERE id = %s
        """, (full_name, email, username, pw_hash, user_id), commit=True)
        print(f"[SUCCESS] Admin account '{username}' updated successfully.")
    else:
        user_id = execute_query("""
            INSERT INTO users (full_name, email, username, password_hash, role, created_at)
            VALUES (%s, %s, %s, %s, 'admin', NOW())
        """, (full_name, email, username, pw_hash), commit=True, return_id=True)
        print(f"[SUCCESS] Admin account '{username}' created successfully with ID {user_id}.")
        
    print("\nAdministrator Credentials:")
    print(f"  Username: {username}")
    print(f"  Email:    {email}")
    print(f"  Password: {password}")
    print(f"  Role:     admin")
    print("==================================================================")

if __name__ == "__main__":
    u = sys.argv[1] if len(sys.argv) > 1 else "admin"
    e = sys.argv[2] if len(sys.argv) > 2 else "admin@organization.com"
    p = sys.argv[3] if len(sys.argv) > 3 else "Admin@123"
    setup_admin(username=u, email=e, password=p)
