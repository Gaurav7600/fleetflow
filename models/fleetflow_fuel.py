# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class FleetflowFuel(models.Model):
    _name = 'fleetflow.fuel'
    _description = 'FleetFlow Fuel & Expense Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'

    name = fields.Char(string='Reference', compute='_compute_name', store=True)
    vehicle_id = fields.Many2one(
        'fleetflow.vehicle',
        string='Vehicle',
        required=True,
        tracking=True,
        ondelete='cascade',
    )
    trip_id = fields.Many2one(
        'fleetflow.trip',
        string='Related Trip',
        tracking=True,
        domain="[('vehicle_id', '=', vehicle_id), ('state', 'in', ['dispatched', 'completed'])]",
    )
    date = fields.Date(string='Date', required=True, default=fields.Date.today, tracking=True)

    liters = fields.Float(string='Liters', tracking=True)
    cost_per_liter = fields.Float(string='Cost per Liter')
    cost = fields.Float(string='Total Fuel Cost', tracking=True, compute='_compute_cost', store=True)

    odometer = fields.Float(string='Odometer at Refuel (km)')
    fuel_station = fields.Char(string='Fuel Station')
    notes = fields.Text(string='Notes')

    log_type = fields.Selection([
        ('fuel', 'Fuel'),
        ('expense', 'Other Expense'),
    ], string='Log Type', default='fuel', required=True)

    expense_description = fields.Char(string='Expense Description')
    manual_cost = fields.Float(string='Expense Amount')

    @api.depends('vehicle_id', 'date', 'log_type')
    def _compute_name(self):
        for rec in self:
            if rec.vehicle_id:
                rec.name = f"{rec.vehicle_id.license_plate or rec.vehicle_id.name} - {rec.log_type or 'fuel'} - {rec.date or ''}"
            else:
                rec.name = 'New Log'

    @api.depends('liters', 'cost_per_liter', 'manual_cost', 'log_type')
    def _compute_cost(self):
        for rec in self:
            if rec.log_type == 'fuel':
                rec.cost = rec.liters * rec.cost_per_liter if rec.cost_per_liter else rec.cost
            else:
                rec.cost = rec.manual_cost
