# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class FleetFlowFuelExpense(models.Model):
    _name = 'ff.fuel.expense'
    _description = 'FleetFlow Fuel & Expense Log'
    _inherit = ['mail.thread']
    _rec_name = 'name'
    _order = 'date desc'

    name = fields.Char(string='Reference', readonly=True, copy=False, default=lambda self: _('New'))
    vehicle_id = fields.Many2one('ff.vehicle', string='Vehicle', required=True, tracking=True)
    trip_id = fields.Many2one('ff.trip', string='Trip ID',
                               domain="[('vehicle_id','=',vehicle_id),('state','=','completed')]")
    driver_id = fields.Many2one('ff.driver', string='Driver')

    expense_type = fields.Selection([
        ('fuel', 'Fuel'),
        ('toll', 'Toll'),
        ('parking', 'Parking'),
        ('other', 'Other'),
    ], string='Type', required=True, default='fuel')

    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    liters = fields.Float(string='Liters', digits=(16, 2))
    cost_per_liter = fields.Float(string='Cost/Liter', digits=(16, 3))
    fuel_cost = fields.Float(string='Fuel Cost')
    misc_expense = fields.Float(string='Misc Expense')
    cost = fields.Float(string='Total Cost', required=True)
    distance_km = fields.Float(string='Distance (km)', digits=(16, 2))
    station = fields.Char(string='Station / Vendor')
    notes = fields.Text(string='Notes')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('ff.fuel.expense') or _('New')
        return super().create(vals_list)

    @api.onchange('liters', 'cost_per_liter')
    def _onchange_compute_cost(self):
        if self.liters and self.cost_per_liter:
            self.fuel_cost = self.liters * self.cost_per_liter
            self.cost = self.fuel_cost + (self.misc_expense or 0)

    @api.onchange('fuel_cost', 'misc_expense')
    def _onchange_total(self):
        self.cost = (self.fuel_cost or 0) + (self.misc_expense or 0)
