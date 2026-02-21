# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class FleetFlowMaintenance(models.Model):
    _name = 'ff.maintenance'
    _description = 'FleetFlow Maintenance / Service Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'service_date desc'

    name = fields.Char(string='Log ID', readonly=True, copy=False, default=lambda self: _('New'))
    vehicle_id = fields.Many2one('ff.vehicle', string='Vehicle Name', required=True, tracking=True)
    service_type = fields.Selection([
        ('oil_change', 'Oil Change'),
        ('tire_rotation', 'Tire Rotation'),
        ('brake_service', 'Brake Service'),
        ('engine_repair', 'Engine Repair'),
        ('transmission', 'Transmission'),
        ('electrical', 'Electrical'),
        ('inspection', 'Annual Inspection'),
        ('other', 'Other'),
    ], string='Date / Service', required=True, default='oil_change')
    service_date = fields.Date(string='Date', required=True, default=fields.Date.today)
    completion_date = fields.Date(string='Completion Date', tracking=True)
    vendor = fields.Char(string='Workshop / Vendor')
    cost = fields.Float(string='Cost')
    odometer_at_service = fields.Float(string='Odometer at Service (km)')
    description = fields.Text(string='Notes')

    state = fields.Selection([
        ('open', 'In Shop'),
        ('done', 'Completed'),
    ], string='Status', default='open', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('ff.maintenance') or _('New')
        records = super().create(vals_list)
        for rec in records:
            if rec.vehicle_id.state == 'on_trip':
                raise UserError(_('Vehicle "%s" is currently On Trip.') % rec.vehicle_id.name)
            rec.vehicle_id.write({'state': 'in_shop'})
        return records

    def action_complete_service(self):
        for rec in self:
            rec.write({'state': 'done', 'completion_date': fields.Date.today()})
            other_open = self.search([
                ('vehicle_id', '=', rec.vehicle_id.id),
                ('state', '=', 'open'),
                ('id', '!=', rec.id),
            ])
            if not other_open:
                rec.vehicle_id.write({'state': 'available'})
