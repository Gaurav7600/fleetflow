# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FleetflowVehicle(models.Model):
    _name = 'fleetflow.vehicle'
    _description = 'FleetFlow Vehicle Registry'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc'

    name = fields.Char(
        string='Vehicle Name / Model',
        required=True,
        tracking=True,
    )
    license_plate = fields.Char(
        string='License Plate',
        required=True,
        copy=False,
        tracking=True,
    )
    vehicle_type = fields.Selection([
        ('truck', 'Truck'),
        ('van', 'Van'),
        ('bike', 'Bike'),
    ], string='Vehicle Type', required=True, default='van', tracking=True)

    region = fields.Char(string='Region', tracking=True)

    max_capacity = fields.Float(
        string='Max Load Capacity (kg)',
        required=True,
        tracking=True,
    )
    odometer = fields.Float(
        string='Odometer (km)',
        tracking=True,
    )
    acquisition_cost = fields.Float(string='Acquisition Cost', tracking=True)

    status = fields.Selection([
        ('available', 'Available'),
        ('on_trip', 'On Trip'),
        ('in_shop', 'In Shop'),
        ('retired', 'Out of Service / Retired'),
    ], string='Status', default='available', required=True, tracking=True)

    out_of_service = fields.Boolean(
        string='Out of Service (Retired)',
        tracking=True,
        compute='_compute_out_of_service',
        inverse='_inverse_out_of_service',
        store=True,
    )

    # Relational
    trip_ids = fields.One2many('fleetflow.trip', 'vehicle_id', string='Trips')
    maintenance_ids = fields.One2many('fleetflow.maintenance', 'vehicle_id', string='Maintenance Logs')
    fuel_ids = fields.One2many('fleetflow.fuel', 'vehicle_id', string='Fuel Logs')

    # Computed financials
    total_fuel_cost = fields.Float(string='Total Fuel Cost', compute='_compute_total_costs', store=True)
    total_maintenance_cost = fields.Float(string='Total Maintenance Cost', compute='_compute_total_costs', store=True)
    total_operational_cost = fields.Float(string='Total Operational Cost', compute='_compute_total_costs', store=True)
    total_revenue = fields.Float(string='Total Revenue', compute='_compute_total_revenue', store=True)
    total_km = fields.Float(string='Total KM (from trips)', compute='_compute_total_km', store=True)
    total_fuel_liters = fields.Float(string='Total Fuel (L)', compute='_compute_total_costs', store=True)
    fuel_efficiency = fields.Float(string='Fuel Efficiency (km/L)', compute='_compute_efficiency', store=True)
    vehicle_roi = fields.Float(string='Vehicle ROI (%)', compute='_compute_roi', store=True)

    trip_count = fields.Integer(string='Trip Count', compute='_compute_trip_count')
    maintenance_count = fields.Integer(string='Maintenance Count', compute='_compute_maintenance_count')

    _sql_constraints = [
        ('license_plate_unique', 'UNIQUE(license_plate)', 'License plate must be unique!'),
    ]

    @api.depends('status')
    def _compute_out_of_service(self):
        for rec in self:
            rec.out_of_service = rec.status == 'retired'

    def _inverse_out_of_service(self):
        for rec in self:
            if rec.out_of_service:
                rec.status = 'retired'
            elif rec.status == 'retired':
                rec.status = 'available'

    @api.depends('fuel_ids.cost', 'fuel_ids.liters', 'maintenance_ids.cost')
    def _compute_total_costs(self):
        for rec in self:
            rec.total_fuel_cost = sum(rec.fuel_ids.mapped('cost'))
            rec.total_fuel_liters = sum(rec.fuel_ids.mapped('liters'))
            rec.total_maintenance_cost = sum(rec.maintenance_ids.mapped('cost'))
            rec.total_operational_cost = rec.total_fuel_cost + rec.total_maintenance_cost

    @api.depends('trip_ids.revenue', 'trip_ids.state')
    def _compute_total_revenue(self):
        for rec in self:
            completed_trips = rec.trip_ids.filtered(lambda t: t.state == 'completed')
            rec.total_revenue = sum(completed_trips.mapped('revenue'))

    @api.depends('trip_ids.distance_km', 'trip_ids.state')
    def _compute_total_km(self):
        for rec in self:
            completed_trips = rec.trip_ids.filtered(lambda t: t.state == 'completed')
            rec.total_km = sum(completed_trips.mapped('distance_km'))

    @api.depends('total_km', 'total_fuel_liters')
    def _compute_efficiency(self):
        for rec in self:
            rec.fuel_efficiency = rec.total_km / rec.total_fuel_liters if rec.total_fuel_liters else 0.0

    @api.depends('total_revenue', 'total_operational_cost', 'acquisition_cost')
    def _compute_roi(self):
        for rec in self:
            if rec.acquisition_cost:
                rec.vehicle_roi = ((rec.total_revenue - rec.total_operational_cost) / rec.acquisition_cost) * 100
            else:
                rec.vehicle_roi = 0.0

    def _compute_trip_count(self):
        for rec in self:
            rec.trip_count = len(rec.trip_ids)

    def _compute_maintenance_count(self):
        for rec in self:
            rec.maintenance_count = len(rec.maintenance_ids)

    def action_set_available(self):
        self.write({'status': 'available'})

    def action_set_retired(self):
        self.write({'status': 'retired'})

    def action_view_trips(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Trips',
            'res_model': 'fleetflow.trip',
            'view_mode': 'list,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }

    def action_view_maintenance(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Maintenance Logs',
            'res_model': 'fleetflow.maintenance',
            'view_mode': 'list,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }
