-- =====================================================================
-- Intelligent IT Asset Lifecycle & License Compliance Platform
-- Database Schema: it_asset_management
-- 14 Tables with Foreign Keys, Constraints, and Indexes
-- =====================================================================

CREATE DATABASE IF NOT EXISTS it_asset_management
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE it_asset_management;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'employee') DEFAULT 'employee',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_username (username),
    INDEX idx_user_email (email),
    INDEX idx_user_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Departments Table
CREATE TABLE IF NOT EXISTS departments (
    department_id INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    INDEX idx_dept_name (department_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Employees Table
CREATE TABLE IF NOT EXISTS employees (
    employee_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE,
    employee_code VARCHAR(30) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    department_id INT,
    designation VARCHAR(100),
    joining_date DATE,
    employee_status ENUM('Active', 'Inactive') DEFAULT 'Active',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE SET NULL,
    INDEX idx_emp_code (employee_code),
    INDEX idx_emp_email (email),
    INDEX idx_emp_dept (department_id),
    INDEX idx_emp_status (employee_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Asset Categories Table
CREATE TABLE IF NOT EXISTS asset_categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    INDEX idx_category_name (category_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Vendors Table
CREATE TABLE IF NOT EXISTS vendors (
    vendor_id INT AUTO_INCREMENT PRIMARY KEY,
    vendor_name VARCHAR(150) NOT NULL,
    contact_person VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    INDEX idx_vendor_name (vendor_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Assets Table
CREATE TABLE IF NOT EXISTS assets (
    asset_id INT AUTO_INCREMENT PRIMARY KEY,
    asset_code VARCHAR(50) NOT NULL UNIQUE,
    asset_name VARCHAR(150) NOT NULL,
    category_id INT,
    vendor_id INT,
    brand VARCHAR(100),
    model_number VARCHAR(100),
    serial_number VARCHAR(100) UNIQUE,
    purchase_date DATE,
    purchase_cost DECIMAL(12, 2),
    warranty_expiry DATE,
    location VARCHAR(150),
    asset_status ENUM('Available', 'Assigned', 'Under Maintenance', 'Retired') DEFAULT 'Available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES asset_categories(category_id) ON DELETE SET NULL,
    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id) ON DELETE SET NULL,
    INDEX idx_asset_code (asset_code),
    INDEX idx_asset_serial (serial_number),
    INDEX idx_asset_status (asset_status),
    INDEX idx_asset_category (category_id),
    INDEX idx_asset_warranty (warranty_expiry)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. Asset Assignments Table
CREATE TABLE IF NOT EXISTS asset_assignments (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    asset_id INT NOT NULL,
    employee_id INT NOT NULL,
    assigned_date DATE NOT NULL,
    return_date DATE,
    assignment_status ENUM('Assigned', 'Returned') DEFAULT 'Assigned',
    remarks TEXT,
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE RESTRICT,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE RESTRICT,
    INDEX idx_assign_asset (asset_id),
    INDEX idx_assign_emp (employee_id),
    INDEX idx_assign_status (assignment_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. Software Catalog Table
CREATE TABLE IF NOT EXISTS software (
    software_id INT AUTO_INCREMENT PRIMARY KEY,
    software_name VARCHAR(150) NOT NULL,
    publisher VARCHAR(100),
    software_category VARCHAR(100),
    version VARCHAR(50),
    INDEX idx_soft_name (software_name),
    INDEX idx_soft_publisher (publisher)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9. Software Licenses Table
CREATE TABLE IF NOT EXISTS software_licenses (
    license_id INT AUTO_INCREMENT PRIMARY KEY,
    software_id INT NOT NULL,
    vendor_id INT,
    license_key VARCHAR(255),
    total_licenses INT NOT NULL,
    purchase_date DATE,
    expiry_date DATE,
    license_cost DECIMAL(12, 2),
    license_status ENUM('Active', 'Expired', 'Cancelled') DEFAULT 'Active',
    FOREIGN KEY (software_id) REFERENCES software(software_id) ON DELETE RESTRICT,
    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id) ON DELETE SET NULL,
    INDEX idx_lic_soft (software_id),
    INDEX idx_lic_vendor (vendor_id),
    INDEX idx_lic_status (license_status),
    INDEX idx_lic_expiry (expiry_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 10. License Assignments Table
CREATE TABLE IF NOT EXISTS license_assignments (
    license_assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    license_id INT NOT NULL,
    employee_id INT NOT NULL,
    assigned_date DATE NOT NULL,
    return_date DATE,
    assignment_status ENUM('Assigned', 'Returned') DEFAULT 'Assigned',
    FOREIGN KEY (license_id) REFERENCES software_licenses(license_id) ON DELETE RESTRICT,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE RESTRICT,
    INDEX idx_lic_assign_lic (license_id),
    INDEX idx_lic_assign_emp (employee_id),
    INDEX idx_lic_assign_status (assignment_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 11. Maintenance Records Table
CREATE TABLE IF NOT EXISTS maintenance_records (
    maintenance_id INT AUTO_INCREMENT PRIMARY KEY,
    asset_id INT NOT NULL,
    maintenance_type VARCHAR(100),
    maintenance_date DATE,
    cost DECIMAL(12, 2),
    description TEXT,
    maintenance_status ENUM('Pending', 'In Progress', 'Completed') DEFAULT 'Pending',
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE RESTRICT,
    INDEX idx_maint_asset (asset_id),
    INDEX idx_maint_status (maintenance_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 12. Purchase Orders Table
CREATE TABLE IF NOT EXISTS purchase_orders (
    purchase_order_id INT AUTO_INCREMENT PRIMARY KEY,
    vendor_id INT,
    order_number VARCHAR(50) UNIQUE,
    order_date DATE,
    total_amount DECIMAL(12, 2),
    order_status ENUM('Pending', 'Approved', 'Received', 'Cancelled') DEFAULT 'Pending',
    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id) ON DELETE SET NULL,
    INDEX idx_po_vendor (vendor_id),
    INDEX idx_po_num (order_number),
    INDEX idx_po_status (order_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 13. Compliance Alerts Table
CREATE TABLE IF NOT EXISTS compliance_alerts (
    alert_id INT AUTO_INCREMENT PRIMARY KEY,
    asset_id INT,
    license_id INT,
    alert_type VARCHAR(100) NOT NULL,
    alert_message TEXT,
    alert_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    alert_status ENUM('Open', 'Resolved') DEFAULT 'Open',
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE,
    FOREIGN KEY (license_id) REFERENCES software_licenses(license_id) ON DELETE CASCADE,
    INDEX idx_alert_status (alert_status),
    INDEX idx_alert_type (alert_type),
    INDEX idx_alert_asset (asset_id),
    INDEX idx_alert_license (license_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 14. Audit Logs Table
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_audit_user (user_id),
    INDEX idx_audit_action (action),
    INDEX idx_audit_time (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
