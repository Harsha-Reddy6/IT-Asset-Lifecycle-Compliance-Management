# Intelligent IT Asset Lifecycle & License Compliance Platform

An enterprise-grade, server-rendered **Python Flask** web application built with a pure **MySQL** relational database backend, vanilla CSS3, and vanilla JavaScript.

---

## 1. Architectural Highlights

- **Server-Rendered MVC**: Traditional Flask web application utilizing Jinja2 templates, native form submissions, session cookies, and redirects.
- **Strictly No ORM / REST**: Direct MySQL integration via `mysql-connector-python` using parameterized queries (`%s`) preventing SQL injection vulnerabilities.
- **Role-Based Access Control (RBAC)**: Distinguishes between **Admin** (full management, procurement, allocations, audits, compliance) and **Employee** (self-service profile, assigned assets, assigned software licenses).
- **Automated Lifecycle & Compliance**:
  - Auto-generation of unique asset tracking codes (`AST-YYYY-XXXX`).
  - Strict allocation business rules (preventing over-allocation or assignment of unavailable/maintenance assets).
  - Automated compliance scanner for expiring asset warranties and software licenses.
  - Comprehensive audit trail recording user and asset events.
  - Dynamic Chart.js visualizations driven by real-time MySQL aggregations.
  - CSV export for hardware assets, software licenses, allocation histories, and audit records.

---

## 2. Technology Stack

| Component | Technology |
|---|---|
| **Backend** | Python 3.12+, Flask 3.x, Werkzeug |
| **Database** | MySQL Server 8.x with connection pooling (`mysql-connector-python`) |
| **Authentication** | Passlib / bcrypt & Werkzeug security with HTTP-only session cookies |
| **Frontend** | HTML5, CSS3 Custom Properties, Vanilla JavaScript (ES6) |
| **Icons & Charts** | Bootstrap Icons, Chart.js (CDN-delivered) |
| **Testing** | pytest 9.x |

---

## 3. Directory Layout

```
IT_Asset_Platform/
│
├── app.py                      # Flask Application entry point & Blueprint registrar
├── config.py                   # App & database configuration loader
├── database.py                 # MySQL pool connection manager & transaction context
├── create_admin.py             # Administrator provisioning script
├── requirements.txt            # Minimal required dependencies
├── README.md                   # System documentation
├── .env.example                # Environment variables template
├── .env                        # Local active configuration
├── .gitignore                  # Git ignore rules
│
├── routes/                     # Blueprint controllers
│   ├── __init__.py
│   ├── auth_routes.py          # /login, /register, /logout, /profile
│   ├── dashboard_routes.py     # /dashboard with real MySQL KPIs & charts
│   ├── employee_routes.py      # /employees CRUD, filters & staff search
│   ├── department_routes.py    # /departments management
│   ├── asset_routes.py         # /assets hardware CRUD & detail view
│   ├── category_routes.py      # /categories equipment classifications
│   ├── assignment_routes.py    # /assignments allocation & return lifecycle
│   ├── vendor_routes.py        # /vendors partner catalog
│   ├── software_routes.py      # /software application catalog
│   ├── license_routes.py       # /licenses seat entitlement tracking
│   ├── license_assignment_routes.py # /license-assignments seat allocation
│   ├── maintenance_routes.py   # /maintenance service ticket management
│   ├── purchase_order_routes.py# /purchase-orders procurement workflow
│   ├── compliance_routes.py    # /compliance scanning & alert resolution
│   └── report_routes.py        # /reports analytics hub & CSV data export
│
├── services/                   # Business domain layer
│   ├── __init__.py
│   ├── asset_service.py        # Asset allocation, return transactions, codes
│   ├── license_service.py      # License capacity checks & allocations
│   ├── compliance_service.py   # Warranty & license compliance scanner
│   └── audit_service.py        # Enterprise audit trail recording
│
├── utils/                      # Helper & security utilities
│   ├── __init__.py
│   ├── auth.py                 # Password hashing, decorators, CSRF
│   ├── validators.py           # Field & datatype validators
│   └── helpers.py              # Pagination, formatting, date calculations
│
├── templates/                  # Server-rendered Jinja2 HTML templates
│   ├── base.html               # Enterprise navy layout, drawer & modal
│   ├── login.html              # Sign-in page with test credentials
│   ├── register.html           # Public employee registration
│   ├── dashboard.html          # Executive KPIs, 5 Chart.js charts, alerts
│   ├── employees.html          # Staff directory & form
│   ├── departments.html        # Department management
│   ├── assets.html             # Equipment inventory, details & forms
│   ├── categories.html         # Categories management
│   ├── assignments.html        # Asset checkout & return modal
│   ├── vendors.html            # Suppliers directory
│   ├── software.html           # Software catalog
│   ├── licenses.html           # License keys & seat utilization
│   ├── license_assignments.html# Seat allocations & revocation modal
│   ├── maintenance.html        # Equipment service tracking
│   ├── purchase_orders.html    # Procurement orders
│   ├── compliance.html         # Compliance dashboard & scan trigger
│   ├── reports.html            # Analytics hub & CSV export
│   └── profile.html            # User account & personal checkouts
│
├── static/
│   ├── css/
│   │   ├── style.css           # Base styles, tables, badges, modals
│   │   ├── dashboard.css       # KPI cards, charts layout, activity feed
│   │   ├── forms.css           # Forms, inputs, filter toolbars, auth card
│   │   └── responsive.css      # Tablet & mobile responsive breakpoints
│   │
│   ├── js/
│   │   ├── main.js             # Mobile drawer, auto-dismiss, delete modals
│   │   ├── dashboard.js        # Chart.js initialization
│   │   ├── assets.js           # Asset filters
│   │   ├── employees.js        # Employee filters
│   │   ├── assignments.js      # Assignment & return modal handlers
│   │   ├── licenses.js         # License return handlers
│   │   ├── compliance.js       # Compliance filters
│   │   └── reports.js          # Reports filters
│   │
│   └── images/
│
├── database/
│   ├── schema.sql              # Complete 14-table DDL schema
│   ├── sample_data.sql         # Seed records with INSERT IGNORE
│   └── views.sql               # Analytical views
│
└── tests/
    ├── __init__.py
    ├── conftest.py             # Pytest fixtures & test clients
    ├── test_auth.py            # Startup, login, register, RBAC
    ├── test_assets.py          # Asset CRUD, uniqueness, details
    ├── test_employees.py       # Employee & department CRUD
    ├── test_assignments.py     # Allocation, return & maintenance
    └── test_licenses.py        # Licenses, compliance scan, CSV export
```

---

## 4. Database Setup

The platform uses the `it_asset_management` database with 14 normalized tables:
1. `users`
2. `employees`
3. `departments`
4. `assets`
5. `asset_categories`
6. `asset_assignments`
7. `vendors`
8. `software`
9. `software_licenses`
10. `license_assignments`
11. `maintenance_records`
12. `purchase_orders`
13. `compliance_alerts`
14. `audit_logs`

To initialize or apply the schema and views manually:
```bash
mysql -u root -p it_asset_management < database/schema.sql
mysql -u root -p it_asset_management < database/sample_data.sql
mysql -u root -p it_asset_management < database/views.sql
```

---

## 5. Environment Configuration

Copy `.env.example` to `.env` and verify database credentials:
```ini
SECRET_KEY=it-asset-platform-enterprise-secret-key-2026-prod-jwt-safe
FLASK_ENV=development
FLASK_DEBUG=1

# MySQL Database Settings
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=Mysql@123
DB_NAME=it_asset_management
```

---

## 6. Installation & Admin Account Creation

1. Install required Python packages:
```bash
pip install -r requirements.txt
```

2. Run the secure Administrator provisioning script:
```bash
python create_admin.py
```
Default Administrator credentials:
- **Username:** `admin`
- **Email:** `admin@organization.com`
- **Password:** `Admin@123`
- **Role:** `admin`

Employee test account:
- **Username:** `johndoe`
- **Password:** `Employee@123`
- **Role:** `employee`

---

## 7. Running the Application

Start the Flask server:
```bash
python app.py
```

Open your browser and navigate to:
**http://127.0.0.1:5000/**

---

## 8. Executing Tests

Run the complete test suite with `pytest`:
```bash
pytest -v
```
All 14 comprehensive test modules verify authentication, access control, asset lifecycle, assignments, return transactions, maintenance workflows, license capacity limits, compliance scanning, and CSV exports against the MySQL database.
