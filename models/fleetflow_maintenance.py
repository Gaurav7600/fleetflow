# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class FleetflowMaintenance(models.Model):
    _name = 'fleetflow.maintenance'
    _description = 'FleetFlow Maintenance & Service Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'

    name = fields.Char(string='Service Description', required=True, tracking=True)
    vehicle_id = fields.Many2one(
        'fleetflow.vehicle',
        string='Vehicle',
        required=True,
        tracking=True,
        ondelete='cascade',
    )
    date = fields.Date(string='Service Date', required=True, default=fields.Date.today, tracking=True)
    maintenance_type = fields.Selection([
        ('preventive', 'Preventive'),
        ('reactive', 'Reactive / Repair'),
        ('inspection', 'Inspection'),
        ('oil_change', 'Oil Change'),
        ('tyre', 'Tyre Change'),
        ('other', 'Other'),
    ], string='Type', required=True, default='preventive', tracking=True)

    cost = fields.Float(string='Cost', tracking=True)
    odometer_at_service = fields.Float(string='Odometer at Service (km)')
    technician = fields.Char(string='Technician / Workshop')
    notes = fields.Text(string='Notes')

    state = fields.Selection([
        ('open', 'In Shop'),
        ('done', 'Completed'),
    ], string='Status', default='open', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            # Auto-logic: Adding a service log sets vehicle to "In Shop"
            if rec.vehicle_id and rec.state == 'open':
                if rec.vehicle_id.status == 'on_trip':
                    raise UserError(_(
                        'Vehicle %s is currently on a trip. Cannot add a maintenance log.'
                    ) % rec.vehicle_id.name)
                rec.vehicle_id.write({'status': 'in_shop'})
        return records

    def action_complete(self):
        for rec in self:
            rec.write({'state': 'done'})
            # Check if vehicle has other open maintenance records
            other_open = self.search([
                ('vehicle_id', '=', rec.vehicle_id.id),
                ('state', '=', 'open'),
                ('id', '!=', rec.id),
            ])
            if not other_open:
                rec.vehicle_id.write({'status': 'available'})

    def action_reopen(self):
        for rec in self:
            rec.write({'state': 'open'})
            rec.vehicle_id.write({'status': 'in_shop'})
