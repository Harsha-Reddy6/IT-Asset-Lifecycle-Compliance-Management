-- =====================================================================
-- Intelligent IT Asset Lifecycle & License Compliance Platform
-- Database Views
-- =====================================================================

USE it_asset_management;

-- View 1: Complete Asset Details with Category, Vendor, and Assignment Status
CREATE OR REPLACE VIEW v_asset_details AS
SELECT 
    a.asset_id,
    a.asset_code,
    a.asset_name,
    a.brand,
    a.model_number,
    a.serial_number,
    a.purchase_date,
    a.purchase_cost,
    a.warranty_expiry,
    a.location,
    a.asset_status,
    a.created_at,
    c.category_id,
    c.category_name,
    v.vendor_id,
    v.vendor_name,
    DATEDIFF(a.warranty_expiry, CURDATE()) AS warranty_days_remaining,
    CASE 
        WHEN a.warranty_expiry < CURDATE() THEN 'Expired'
        WHEN DATEDIFF(a.warranty_expiry, CURDATE()) <= 30 THEN 'Expiring Soon'
        ELSE 'Active'
    END AS warranty_status
FROM assets a
LEFT JOIN asset_categories c ON a.category_id = c.category_id
LEFT JOIN vendors v ON a.vendor_id = v.vendor_id;

-- View 2: Active Asset Assignments with Employee and Department Info
CREATE OR REPLACE VIEW v_active_assignments AS
SELECT 
    aa.assignment_id,
    aa.asset_id,
    a.asset_code,
    a.asset_name,
    a.serial_number,
    e.employee_id,
    e.employee_code,
    e.full_name AS employee_name,
    e.email AS employee_email,
    d.department_name,
    aa.assigned_date,
    aa.assignment_status,
    aa.remarks
FROM asset_assignments aa
JOIN assets a ON aa.asset_id = a.asset_id
JOIN employees e ON aa.employee_id = e.employee_id
LEFT JOIN departments d ON e.department_id = d.department_id
WHERE aa.assignment_status = 'Assigned';

-- View 3: Software License Utilization and Seat Capacity
CREATE OR REPLACE VIEW v_license_utilization AS
SELECT 
    l.license_id,
    s.software_name,
    s.publisher,
    s.version,
    l.license_key,
    l.total_licenses,
    COUNT(CASE WHEN la.assignment_status = 'Assigned' THEN 1 END) AS assigned_licenses,
    (l.total_licenses - COUNT(CASE WHEN la.assignment_status = 'Assigned' THEN 1 END)) AS available_licenses,
    l.purchase_date,
    l.expiry_date,
    l.license_cost,
    l.license_status,
    v.vendor_name,
    DATEDIFF(l.expiry_date, CURDATE()) AS days_to_expiry,
    CASE
        WHEN l.license_status = 'Expired' OR l.expiry_date < CURDATE() THEN 'Expired'
        WHEN DATEDIFF(l.expiry_date, CURDATE()) <= 30 THEN 'Expiring Soon'
        ELSE 'Active'
    END AS computed_compliance_status
FROM software_licenses l
JOIN software s ON l.software_id = s.software_id
LEFT JOIN vendors v ON l.vendor_id = v.vendor_id
LEFT JOIN license_assignments la ON l.license_id = la.license_id
GROUP BY l.license_id, s.software_name, s.publisher, s.version, l.license_key, 
         l.total_licenses, l.purchase_date, l.expiry_date, l.license_cost, 
         l.license_status, v.vendor_name;

-- View 4: Compliance Summary
CREATE OR REPLACE VIEW v_compliance_summary AS
SELECT 
    alert_type,
    alert_status,
    COUNT(*) AS total_alerts
FROM compliance_alerts
GROUP BY alert_type, alert_status;
