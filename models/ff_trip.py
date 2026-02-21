# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class FleetFlowTrip(models.Model):
    _name = 'ff.trip'
    _description = 'FleetFlow Trip'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'scheduled_date desc, name desc'

    name = fields.Char(string='Trip Reference', readonly=True, copy=False, default=lambda self: _('New'))
    vehicle_id = fields.Many2one('ff.vehicle', string='Vehicle', required=True,
                                  domain="[('state','=','available')]", tracking=True)
    driver_id = fields.Many2one('ff.driver', string='Driver', required=True,
                                 domain="[('state','in',['available']),('license_expired','=',False)]",
                                 tracking=True)
    fleet_type = fields.Selection(related='vehicle_id.vehicle_type', string='Fleet Type', store=True)

    origin = fields.Char(string='Origin Address', required=True)
    destination = fields.Char(string='Destination', required=True)
    scheduled_date = fields.Datetime(string='Scheduled Departure', required=True, tracking=True)
    actual_departure = fields.Datetime(string='Actual Departure')
    actual_arrival = fields.Datetime(string='Actual Arrival')

    cargo_description = fields.Text(string='Cargo Description')
    cargo_weight = fields.Float(string='Cargo Weight (kg)', required=True)
    vehicle_capacity = fields.Float(related='vehicle_id.max_load_capacity', string='Max Capacity (kg)', readonly=True)
    estimated_fuel_cost = fields.Float(string='Estimated Fuel Cost')
    capacity_ok = fields.Boolean(string='Capacity OK', compute='_compute_capacity_ok')

    revenue = fields.Float(string='Trip Revenue')
    distance_km = fields.Float(string='Distance (km)')
    odometer_start = fields.Float(string='Odometer Start (km)')
    odometer_end = fields.Float(string='Odometer End (km)')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('dispatched', 'Dispatched'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, index=True)

    notes = fields.Text(string='Notes')

    @api.depends('cargo_weight', 'vehicle_id.max_load_capacity')
    def _compute_capacity_ok(self):
        for t in self:
            t.capacity_ok = (t.cargo_weight <= t.vehicle_id.max_load_capacity
                             if t.vehicle_id and t.cargo_weight else True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('ff.trip') or _('New')
        return super().create(vals_list)

    @api.constrains('cargo_weight', 'vehicle_id')
    def _check_cargo_weight(self):
        for t in self:
            if t.vehicle_id and t.cargo_weight > t.vehicle_id.max_load_capacity:
                raise ValidationError(_(
                    'Cargo weight (%(w)s kg) exceeds vehicle max capacity (%(c)s kg) for "%(v)s".',
                    w=t.cargo_weight, c=t.vehicle_id.max_load_capacity, v=t.vehicle_id.name,
                ))

    def action_dispatch(self):
        for trip in self:
            if trip.state != 'draft':
                raise UserError(_('Only draft trips can be dispatched.'))
            if trip.cargo_weight > trip.vehicle_id.max_load_capacity:
                raise ValidationError(_('Cannot dispatch: cargo weight exceeds vehicle capacity.'))
            trip.driver_id._check_assignment_eligibility(vehicle_type=trip.vehicle_id.vehicle_type)
            trip.vehicle_id.write({'state': 'on_trip'})
            trip.driver_id.write({'state': 'on_duty'})
            trip.write({'state': 'dispatched', 'actual_departure': fields.Datetime.now()})

    def action_complete(self):
        for trip in self:
            if trip.state != 'dispatched':
                raise UserError(_('Only dispatched trips can be completed.'))
            trip.vehicle_id.write({'state': 'available'})
            trip.driver_id.write({'state': 'available'})
            if trip.odometer_end:
                trip.vehicle_id.write({'odometer': trip.odometer_end})
            if trip.driver_id.safety_score < 100:
                trip.driver_id.safety_score = min(100, trip.driver_id.safety_score + 0.5)
            trip.write({'state': 'completed', 'actual_arrival': fields.Datetime.now()})

    def action_cancel(self):
        for trip in self:
            if trip.state == 'completed':
                raise UserError(_('Completed trips cannot be cancelled.'))
            if trip.state == 'dispatched':
                trip.vehicle_id.write({'state': 'available'})
                trip.driver_id.write({'state': 'available'})
            trip.write({'state': 'cancelled'})

    def action_reset_draft(self):
        for trip in self:
            if trip.state != 'cancelled':
                raise UserError(_('Only cancelled trips can be reset to draft.'))
            trip.write({'state': 'draft'})
