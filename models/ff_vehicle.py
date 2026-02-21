# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class FleetFlowVehicle(models.Model):
    _name = 'ff.vehicle'
    _description = 'FleetFlow Vehicle'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'name asc'

    # ── Identification ────────────────────────────────────────────────────────
    name = fields.Char(string='Vehicle Name / Model', required=True, tracking=True)
    license_plate = fields.Char(string='License Plate', required=True, copy=False, tracking=True)
    vehicle_type = fields.Selection([
        ('truck', 'Truck'),
        ('van', 'Van'),
        ('bike', 'Bike'),
        ('other', 'Other'),
    ], string='Type', required=True, default='van', tracking=True)
    region = fields.Char(string='Region / Base')

    # ── Capacity & Odometer ───────────────────────────────────────────────────
    max_load_capacity = fields.Float(string='Max Load Capacity (kg)', required=True)
    odometer = fields.Float(string='Odometer (km)', tracking=True)
    acquisition_cost = fields.Float(string='Acquisition Cost')
    acquisition_date = fields.Date(string='Acquisition Date')

    # ── Status ────────────────────────────────────────────────────────────────
    state = fields.Selection([
        ('available', 'Available'),
        ('on_trip', 'On Trip'),
        ('in_shop', 'In Shop'),
        ('retired', 'Retired'),
    ], string='Status', default='available', tracking=True, index=True)

    out_of_service = fields.Boolean(string='Out of Service (Retired)', tracking=True)
    active = fields.Boolean(default=True)

    # ── Relations ─────────────────────────────────────────────────────────────
    trip_ids = fields.One2many('ff.trip', 'vehicle_id', string='Trips')
    maintenance_ids = fields.One2many('ff.maintenance', 'vehicle_id', string='Service Logs')
    fuel_expense_ids = fields.One2many('ff.fuel.expense', 'vehicle_id', string='Fuel / Expenses')

    # ── Computed Financials ───────────────────────────────────────────────────
    total_fuel_cost = fields.Float(string='Total Fuel Cost', compute='_compute_costs', store=True)
    total_maintenance_cost = fields.Float(string='Total Maintenance Cost', compute='_compute_costs', store=True)
    total_operational_cost = fields.Float(string='Total Operational Cost', compute='_compute_costs', store=True)
    total_revenue = fields.Float(string='Total Revenue', compute='_compute_costs', store=True)
    vehicle_roi = fields.Float(string='ROI (%)', compute='_compute_roi', store=True, digits=(16, 2))
    trip_count = fields.Integer(string='Trips', compute='_compute_trip_count')
    fuel_efficiency = fields.Float(string='Fuel Efficiency (km/L)', compute='_compute_fuel_efficiency', store=True, digits=(16, 2))

    # ── SQL Constraints ───────────────────────────────────────────────────────
    _sql_constraints = [
        ('license_plate_uniq', 'UNIQUE(license_plate)', 'License plate must be unique!'),
    ]

    @api.depends('fuel_expense_ids.cost', 'fuel_expense_ids.expense_type',
                 'maintenance_ids.cost', 'trip_ids.revenue')
    def _compute_costs(self):
        for v in self:
            v.total_fuel_cost = sum(e.cost for e in v.fuel_expense_ids if e.expense_type == 'fuel')
            v.total_maintenance_cost = sum(m.cost for m in v.maintenance_ids)
            v.total_operational_cost = v.total_fuel_cost + v.total_maintenance_cost
            v.total_revenue = sum(t.revenue for t in v.trip_ids if t.state == 'completed')

    @api.depends('total_revenue', 'total_operational_cost', 'acquisition_cost')
    def _compute_roi(self):
        for v in self:
            if v.acquisition_cost:
                v.vehicle_roi = ((v.total_revenue - v.total_operational_cost) / v.acquisition_cost) * 100
            else:
                v.vehicle_roi = 0.0

    def _compute_trip_count(self):
        for v in self:
            v.trip_count = len(v.trip_ids)

    @api.depends('fuel_expense_ids.liters', 'fuel_expense_ids.distance_km')
    def _compute_fuel_efficiency(self):
        for v in self:
            liters = sum(e.liters for e in v.fuel_expense_ids if e.expense_type == 'fuel' and e.liters)
            km = sum(e.distance_km for e in v.fuel_expense_ids if e.distance_km)
            v.fuel_efficiency = (km / liters) if liters else 0.0

    @api.constrains('max_load_capacity')
    def _check_capacity(self):
        for v in self:
            if v.max_load_capacity <= 0:
                raise ValidationError(_('Max Load Capacity must be greater than 0.'))

    @api.onchange('out_of_service')
    def _onchange_out_of_service(self):
        if self.out_of_service:
            self.state = 'retired'

    def action_set_available(self):
        self.write({'state': 'available'})

    def action_set_retired(self):
        self.write({'state': 'retired', 'out_of_service': True})

    def action_view_trips(self):
        return {
            'name': _('Trips'),
            'type': 'ir.actions.act_window',
            'res_model': 'ff.trip',
            'view_mode': 'list,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }
