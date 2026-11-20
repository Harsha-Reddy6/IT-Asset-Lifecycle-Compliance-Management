-- =====================================================================
-- Intelligent IT Asset Lifecycle & License Compliance Platform
-- Sample Data Seed Script (Safe Execution via INSERT IGNORE)
-- =====================================================================

USE it_asset_management;

-- Departments
INSERT IGNORE INTO departments (department_id, department_name, description) VALUES
(1, 'Engineering', 'Software Development, QA, Cloud Infrastructure and DevOps'),
(2, 'IT Support', 'Internal IT helpdesk, workstation provisioning, and network operations'),
(3, 'Human Resources', 'Talent acquisition, employee relations, and HR compliance'),
(4, 'Finance & Accounting', 'Financial reporting, payroll, and asset depreciation'),
(5, 'Marketing & Sales', 'Digital marketing, corporate communications, and enterprise sales');

-- Asset Categories
INSERT IGNORE INTO asset_categories (category_id, category_name, description) VALUES
(1, 'Laptops', 'High-performance engineering and standard business laptops'),
(2, 'Desktop Workstations', 'Tower PCs and graphics workstations'),
(3, 'Servers', 'Rackmount servers, storage units, and datacenter hardware'),
(4, 'Monitors & Displays', '4K and Ultra-wide external monitors'),
(5, 'Networking Hardware', 'Routers, managed switches, and Wi-Fi access points'),
(6, 'Mobile Devices', 'Test phones, tablets, and mobile field units');

-- Vendors
INSERT IGNORE INTO vendors (vendor_id, vendor_name, contact_person, email, phone, address) VALUES
(1, 'Dell Technologies', 'Michael Stevens', 'sales@dell-enterprise.com', '+1-800-456-3355', 'One Dell Way, Round Rock, TX 78682'),
(2, 'Apple Inc.', 'Katherine Vance', 'business@apple-enterprise.com', '+1-800-854-3680', 'One Apple Park Way, Cupertino, CA 95014'),
(3, 'Lenovo Global', 'David Chen', 'enterprise@lenovo.com', '+1-855-253-6686', '1009 Think Place, Morrisville, NC 27560'),
(4, 'Cisco Systems', 'Angela Martinez', 'sales@cisco-direct.com', '+1-800-553-6387', '170 West Tasman Dr, San Jose, CA 95134'),
(5, 'Microsoft Licensing Partner', 'Robert Wilson', 'licensing@msftpartner.com', '+1-800-642-7676', 'One Microsoft Way, Redmond, WA 98052');

-- Software Catalog
INSERT IGNORE INTO software (software_id, software_name, publisher, software_category, version) VALUES
(1, 'Microsoft 365 Enterprise E5', 'Microsoft', 'Productivity Suite', '2026 / Cloud'),
(2, 'JetBrains All Products Pack', 'JetBrains', 'Developer Tools', '2024.2'),
(3, 'Adobe Creative Cloud All Apps', 'Adobe', 'Design & Media', '2024'),
(4, 'Docker Desktop Enterprise', 'Docker Inc.', 'DevOps & Containers', '4.32'),
(5, 'CrowdStrike Falcon Endpoint', 'CrowdStrike', 'Cybersecurity', '7.15');

-- Software Licenses
INSERT IGNORE INTO software_licenses (license_id, software_id, vendor_id, license_key, total_licenses, purchase_date, expiry_date, license_cost, license_status) VALUES
(1, 1, 5, 'MS365-E5-9988-7766-5544', 25, '2024-01-01', '2027-01-01', 12500.00, 'Active'),
(2, 2, 5, 'JB-ENT-4433-2211-0099', 10, '2024-03-01', '2026-11-20', 4990.00, 'Active'),
(3, 3, 5, 'ADBE-CC-8877-6655-4433', 5, '2023-11-01', '2024-11-01', 3995.00, 'Expired'),
(4, 4, 1, 'DKR-ENT-1122-3344-5566', 15, '2024-06-01', '2025-06-01', 3600.00, 'Active');

-- Assets
INSERT IGNORE INTO assets (asset_id, asset_code, asset_name, category_id, vendor_id, brand, model_number, serial_number, purchase_date, purchase_cost, warranty_expiry, location, asset_status) VALUES
(1, 'AST-2024-001', 'Dell XPS 15 9530', 1, 1, 'Dell', 'XPS-9530-I7', 'DELL-SN-998811', '2024-02-10', 2199.00, '2027-02-10', 'San Francisco HQ - Desk 3A', 'Assigned'),
(2, 'AST-2024-002', 'MacBook Pro 16 M3 Max', 1, 2, 'Apple', 'MBP-16-M3M', 'APPL-SN-332211', '2024-04-12', 3499.00, '2027-04-12', 'San Francisco HQ - Desk 4B', 'Assigned'),
(3, 'AST-2024-003', 'ThinkPad X1 Carbon Gen 11', 1, 3, 'Lenovo', 'X1C-GEN11', 'LENO-SN-774411', '2024-05-20', 1850.00, '2026-05-20', 'New York Office - Floor 2', 'Assigned'),
(4, 'AST-2024-004', 'Dell PowerEdge R750 Server', 3, 1, 'Dell', 'R750-2U', 'DELL-SRV-882200', '2023-01-15', 7899.00, '2026-01-15', 'Datacenter Rack 04', 'Available'),
(5, 'AST-2024-005', 'Cisco Catalyst 9300 Switch', 5, 4, 'Cisco', 'C9300-48P', 'CISCO-SW-556677', '2023-08-01', 4500.00, '2026-08-01', 'IDF Closet - Floor 3', 'Available'),
(6, 'AST-2024-006', 'Dell UltraSharp 32 4K Monitor', 4, 1, 'Dell', 'U3223QE', 'DELL-MON-441122', '2024-02-15', 899.00, '2027-02-15', 'San Francisco HQ - Desk 3A', 'Assigned'),
(7, 'AST-2024-007', 'Apple Studio Display 27', 4, 2, 'Apple', 'MK0U3LL/A', 'APPL-MON-119933', '2024-04-15', 1599.00, '2027-04-15', 'San Francisco HQ - Desk 4B', 'Available'),
(8, 'AST-2024-008', 'ThinkPad T14 Gen 4', 1, 3, 'Lenovo', 'T14-GEN4', 'LENO-SN-990022', '2022-06-10', 1200.00, '2024-06-10', 'Storage Room B', 'Under Maintenance');

-- Maintenance Records
INSERT IGNORE INTO maintenance_records (maintenance_id, asset_id, maintenance_type, maintenance_date, cost, description, maintenance_status) VALUES
(1, 8, 'Battery & Keyboard Replacement', '2024-10-05', 180.00, 'Swollen battery replaced and internal fan cleaned', 'Pending'),
(2, 4, 'Firmware & RAID Controller Update', '2024-08-12', 0.00, 'Scheduled BIOS and firmware upgrade to v2.4.1', 'Completed');

-- Purchase Orders
INSERT IGNORE INTO purchase_orders (purchase_order_id, vendor_id, order_number, order_date, total_amount, order_status) VALUES
(1, 1, 'PO-2024-001', '2024-01-20', 15200.00, 'Received'),
(2, 2, 'PO-2024-002', '2024-03-10', 12500.00, 'Received'),
(3, 4, 'PO-2024-003', '2024-07-01', 8900.00, 'Approved'),
(4, 5, 'PO-2024-004', '2024-09-15', 6400.00, 'Pending');
