Video Link : https://drive.google.com/file/d/14Si0J1EhZDb0g0L99iNaNFI4r9sFeiRH/view?usp=sharing


# FleetFlow – Fleet & Logistics Management System

A modular, enterprise-grade fleet management platform for Odoo 18 that replaces manual logbooks with a centralized, rule-based digital hub for complete fleet lifecycle management.

## 📋 Overview

FleetFlow is a comprehensive fleet management solution designed to streamline operations across vehicle management, trip dispatching, maintenance tracking, fuel logging, driver safety, and financial analytics. It provides a 360° view of fleet health with real-time KPIs, automated workflows, and role-based access control.

## ✨ Key Features

### 1. **Command Center Dashboard**
- Real-time KPIs: Active Fleet, Maintenance Status, Vehicle Utilization, Cargo Overview
- Visual analytics with comprehensive fleet health monitoring
- Customizable widgets for role-specific insights

### 2. **Vehicle Registry & Asset Management**
- Complete vehicle lifecycle tracking
- Asset records with maintenance history
- Out-of-Service status management
- Digital vehicle registration

### 3. **Trip Dispatch & Management**
- Workflow states: Draft → Dispatched → Completed → Cancelled
- Route planning and assignment
- Trip status tracking
- Historical trip analytics

### 4. **Maintenance & Service**
- Preventive maintenance scheduling
- Service log tracking
- Automatic "In Shop" status management
- Maintenance history per vehicle

### 5. **Fuel Expense Management**
- Fuel expense logging and tracking
- Cost analysis per vehicle
- Fuel efficiency metrics (km/L)
- Expense reports and reconciliation

### 6. **Driver Performance & Safety**
- Driver profiles with safety scores
- License expiry tracking with compliance blocking
- Safety incident logging
- Performance analytics

### 7. **Operational Analytics & Reporting**
- ROI calculations
- Fuel efficiency metrics
- Cost per kilometer analysis
- CSV export functionality
- Financial reporting tools

## 🏛️ Architecture

### Module Structure

```
fleetflow/
├── models/                      # Core data models
│   ├── ff_driver.py            # Driver profiles & safety
│   ├── ff_vehicle.py           # Vehicle asset management
│   ├── ff_trip.py              # Trip lifecycle
│   ├── ff_maintenance.py       # Maintenance tracking
│   ├── ff_fuel_expense.py      # Fuel & expense logging
│   └── __init__.py
├── views/                       # User interface layer
│   ├── ff_driver_views.xml
│   ├── ff_vehicle_views.xml
│   ├── ff_trip_views.xml
│   ├── ff_maintenance_views.xml
│   ├── ff_fuel_expense_views.xml
│   ├── ff_dashboard_views.xml
│   ├── ff_analytics_views.xml
│   └── ff_menu.xml            # Navigation menu
├── security/                    # Access control
│   ├── fleetflow_groups.xml    # User groups & permissions
│   └── ir.model.access.csv     # Model-level access rules
├── data/
│   └── fleetflow_sequence.xml  # Document numbering sequences
└── static/
    └── src/
        ├── js/                  # JavaScript components
        │   ├── ff_dashboard.js
        │   └── ff_analytics.js
        ├── css/                 # Stylesheets
        │   ├── fleetflow.css
        │   ├── ff_dashboard.css
        │   └── ff_analytics.css
        └── xml/                 # Widget templates
            ├── ff_dashboard.xml
            └── ff_analytics.xml
```

## 👥 User Roles & Permissions

FleetFlow implements Role-Based Access Control (RBAC) with four primary user groups:

| Role | Permissions | Access |
|------|-------------|--------|
| **Fleet Manager** | View all records, Create/Edit vehicles, Review analytics, Approve maintenance | Full module access |
| **Dispatcher** | Create/Manage trips, View vehicle status, Assign trips to drivers | Trip & vehicle dispatch |
| **Safety Officer** | Monitor driver profiles, Review incidents, License compliance tracking | Driver & safety records |
| **Finance Officer** | Expense tracking, Fuel reports, Cost analysis, Financial statements | Expense & analytics |

Permissions are managed via:
- `security/fleetflow_groups.xml` – Group definitions
- `security/ir.model.access.csv` – Model-level CRUD access control

## 🗄️ Core Data Models

### **ff_vehicle.py**
- Vehicle assets, specifications, and registration
- Maintenance & fuel cost tracking
- Out-of-service status management
- Vehicle lifecycle management

### **ff_driver.py**
- Driver profiles and contact details
- License information with expiry tracking
- Safety score calculation
- Performance metrics

### **ff_trip.py**
- Trip lifecycle and workflow states
- Route details and distance tracking
- Driver assignment and scheduling
- Trip history and analytics

### **ff_maintenance.py**
- Maintenance records and service logs
- Scheduled and reactive maintenance
- Service history per vehicle
- Cost tracking by maintenance type

### **ff_fuel_expense.py**
- Fuel expense logging and tracking
- Fuel efficiency calculations (km/L)
- Cost per vehicle analysis
- Operational expense aggregation

## 🚀 Installation

### Prerequisites
- Odoo 18.0
- Python 3.10+
- PostgreSQL (as per Odoo requirements)

### Steps

1. **Clone the repository into your Odoo addons directory:**
   ```bash
   cd /path/to/odoo/addons
   git clone https://github.com/Gaurav7600/fleetflow.git
   ```

2. **Update Odoo app list:**
   - Navigate to **Apps > Update Apps List**
   - Click the "Update Apps List" button

3. **Install FleetFlow:**
   - Search for "FleetFlow" in the Apps menu
   - Click **Install**

4. **Configure User Groups:**
   - Go to **Settings > Users & Companies > Groups**
   - Assign users to appropriate FleetFlow groups

5. **Start using FleetFlow:**
   - Access via **FleetFlow > Dashboard** in the main menu

## 💻 Development

### Setting Up a Development Environment

1. **Clone and activate Odoo:**
   ```bash
   git clone https://github.com/odoo/odoo.git
   cd odoo
   git checkout 18.0
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Link FleetFlow module:**
   ```bash
   ln -s /path/to/fleetflow /path/to/odoo/addons/fleetflow
   ```

4. **Run Odoo in development mode:**
   ```bash
   python odoo-bin --addons-path=/path/to/addons -d database_name --dev=all
   ```

### Key Files for Development

- **Models & Business Logic:** `models/*.py`
- **UI & Forms:** `views/*.xml`
- **Styling:** `static/src/css/`
- **Dashboards & Reports:** `static/src/js/`, `static/src/xml/`

## 📊 Workflows & Processes

### Trip Workflow
```
Draft → Dispatched → In Progress → Completed
                  ↓
              Cancelled
```

### Maintenance Workflow
```
Planned → Scheduled → In Shop → Completed → Verified
```

### Vehicle Status
```
Active ↔ Out-of-Service → Retired
```

## 📈 Reporting & Analytics

### Available Reports
1. **Fleet Health Dashboard** – Real-time KPI overview
2. **Fuel Efficiency Report** – km/L analysis by vehicle
3. **Maintenance Schedule** – Upcoming services and past records
4. **Financial Report** – Cost per vehicle, ROI analysis
5. **Driver Safety Report** – Incident tracking and compliance

All reports support **CSV export** for external analysis.

## 🔒 Security Features

- **Row-Level Security:** Users see only relevant records based on roles
- **Model-Level Access Control:** CRUD permissions by group
- **Audit Trail:** All changes tracked via Odoo's native audit log
- **License Compliance:** Automatic blocking of expired driver licenses
- **Field-Level Encryption:** Sensitive data protected (optional)

## 📝 Constants & Sequences

### Document Numbering
- **Trips:** TRP/YYYY/0001, TRP/YYYY/0002, ...
- **Maintenance:** MNT/YYYY/0001, MNT/YYYY/0002, ...
- **Expenses:** EXP/YYYY/0001, EXP/YYYY/0002, ...

Configured in: `data/fleetflow_sequence.xml`

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| Module not appearing in Apps | Run "Update Apps List" from the Apps menu |
| Permission denied errors | Check user group assignments in Settings |
| Dashboard not loading | Clear browser cache; check JS console for errors |
| Missing menu items | Verify `ff_menu.xml` is properly loaded |


## 👨‍💻 Authors

**FleetFlow Development Team**

---

**Version:** 18.0.2.0.0  
**Last Updated:** February 21, 2026
