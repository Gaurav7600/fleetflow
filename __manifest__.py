# -*- coding: utf-8 -*-
{
    'name': 'FleetFlow – Fleet & Logistics Management',
    'version': '18.0.2.0.0',
    'category': 'Fleet',
    'summary': 'Complete fleet lifecycle, dispatching, driver safety & financial analytics',
    'description': """
FleetFlow – Modular Fleet & Logistics Management System
=======================================================
Replaces manual logbooks with a centralized rule-based digital hub:

Pages (matching wireframe blueprint):
  1. Login & Authentication (RBAC: Manager / Dispatcher / Safety / Finance)
  2. Command Center Dashboard (KPIs: Active Fleet, Maintenance, Utilization, Cargo)
  3. Vehicle Registry – Asset Management (CRUD + Out-of-Service toggle)
  4. Trip Dispatcher & Management (Draft→Dispatched→Completed→Cancelled)
  5. Maintenance & Service Logs (auto In Shop status)
  6. Expense & Fuel Logging (Total Operational Cost per vehicle)
  7. Driver Performance & Safety Profiles (license expiry block, safety score)
  8. Operational Analytics & Financial Reports (ROI, km/L, CSV export)
    """,
    'author': 'FleetFlow',
    'depends': ['base', 'mail', 'web'],
    'data': [
        # Security first
        'security/fleetflow_groups.xml',
        'security/ir.model.access.csv',
        # Sequences
        'data/fleetflow_sequence.xml',
        # Views – ordered by dependency
        'views/ff_vehicle_views.xml',
        'views/ff_driver_views.xml',
        'views/ff_maintenance_views.xml',
        'views/ff_fuel_expense_views.xml',
        'views/ff_trip_views.xml',
        'views/ff_dashboard_views.xml',
        'views/ff_analytics_views.xml',
        'views/ff_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'fleetflow/static/src/css/fleetflow.css',
            'fleetflow/static/src/css/ff_dashboard.css',
            'fleetflow/static/src/xml/ff_dashboard.xml',
            'fleetflow/static/src/js/ff_dashboard.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
