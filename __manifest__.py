# -*- coding: utf-8 -*-
{
    'name': 'FleetFlow - Modular Fleet & Logistics Management',
    'version': '18.0.1.0.0',
    'category': 'Fleet',
    'summary': 'Centralized fleet lifecycle, dispatch, driver safety, and financial tracking',
    'description': """
FleetFlow: Modular Fleet & Logistics Management System
======================================================
- Vehicle Registry (Asset Management)
- Trip Dispatcher & Management with cargo validation
- Maintenance & Service Logs (auto status switching)
- Fuel & Expense Logging with cost calculations
- Driver Performance & Safety Profiles
- Operational Analytics & Financial Reports
- Role-Based Access Control (Manager, Dispatcher, Safety Officer, Financial Analyst)
    """,
    'author': 'FleetFlow',
    'depends': ['base', 'mail', 'web'],
    'data': [
        'security/fleetflow_security.xml',
        'security/ir.model.access.csv',
        'data/fleetflow_data.xml',
        'views/fleetflow_vehicle_views.xml',
        'views/fleetflow_driver_views.xml',
        'views/fleetflow_trip_views.xml',
        'views/fleetflow_maintenance_views.xml',
        'views/fleetflow_fuel_views.xml',
        'views/fleetflow_analytics_views.xml',
        'views/fleetflow_dashboard_views.xml',
        'views/fleetflow_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'fleetflow/static/src/css/fleetflow.css',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
