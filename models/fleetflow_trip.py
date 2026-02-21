# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class FleetflowTrip(models.Model):
    _name = 'fleetflow.trip'
    _description = 'FleetFlow Trip'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Trip Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
    )
    origin = fields.Char(string='Origin / Point A', required=True)
    destination = fields.Char(string='Destination / Point B', required=True)

    vehicle_id = fields.Many2one(
        'fleetflow.vehicle',
        string='Vehicle',
        required=True,
        domain=[('status', 'in', ['available']), ('out_of_service', '=', False)],
        tracking=True,
    )
    driver_id = fields.Many2one(
        'fleetflow.driver',
        string='Driver',
        required=True,
        domain=[('status', 'in', ['on_duty', 'off_duty']), ('license_valid', '=', True)],
        tracking=True,
    )

    cargo_weight = fields.Float(string='Cargo Weight (kg)', required=True)
    cargo_description = fields.Text(string='Cargo Description')
    revenue = fields.Float(string='Trip Revenue')

    scheduled_date = fields.Datetime(string='Scheduled Date', required=True)
    dispatched_date = fields.Datetime(string='Dispatched Date', readonly=True)
    completed_date = fields.Datetime(string='Completed Date', readonly=True)

    odometer_start = fields.Float(string='Odometer Start (km)')
    odometer_end = fields.Float(string='Odometer End (km)')
    distance_km = fields.Float(string='Distance (km)', compute='_compute_distance', store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('dispatched', 'Dispatched'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)

    notes = fields.Text(string='Notes')

    # Linked fuel log from trip completion
    fuel_log_ids = fields.One2many('fleetflow.fuel', 'trip_id', string='Fuel Logs')

    @api.depends('odometer_start', 'odometer_end')
    def _compute_distance(self):
        for rec in self:
            if rec.odometer_end > rec.odometer_start:
                rec.distance_km = rec.odometer_end - rec.odometer_start
            else:
                rec.distance_km = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('fleetflow.trip') or _('New')
        return super().create(vals_list)

    @api.constrains('cargo_weight', 'vehicle_id')
    def _check_cargo_capacity(self):
        for rec in self:
            if rec.vehicle_id and rec.cargo_weight > rec.vehicle_id.max_capacity:
                raise ValidationError(_(
                    'Cargo weight (%(weight)s kg) exceeds vehicle maximum capacity (%(cap)s kg) for %(vehicle)s!',
                    weight=rec.cargo_weight,
                    cap=rec.vehicle_id.max_capacity,
                    vehicle=rec.vehicle_id.name,
                ))

    @api.constrains('driver_id', 'vehicle_id')
    def _check_driver_vehicle_compatibility(self):
        for rec in self:
            if rec.driver_id and rec.vehicle_id:
                ok, msg = rec.driver_id.is_available_for_vehicle(rec.vehicle_id.vehicle_type)
                if not ok:
                    raise ValidationError(msg)

    def action_dispatch(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Only draft trips can be dispatched.'))
            # Re-validate
            rec._check_cargo_capacity()
            rec._check_driver_vehicle_compatibility()
            rec.write({
                'state': 'dispatched',
                'dispatched_date': fields.Datetime.now(),
                'odometer_start': rec.vehicle_id.odometer,
            })
            rec.vehicle_id.write({'status': 'on_trip'})
            rec.driver_id.write({'status': 'on_trip'})

    def action_complete(self):
        for rec in self:
            if rec.state != 'dispatched':
                raise UserError(_('Only dispatched trips can be completed.'))
            rec.write({
                'state': 'completed',
                'completed_date': fields.Datetime.now(),
            })
            if rec.odometer_end:
                rec.vehicle_id.write({
                    'odometer': rec.odometer_end,
                    'status': 'available',
                })
            else:
                rec.vehicle_id.write({'status': 'available'})
            # Return driver to on_duty
            rec.driver_id.write({'status': 'on_duty'})

    def action_cancel(self):
        for rec in self:
            if rec.state == 'completed':
                raise UserError(_('Completed trips cannot be cancelled.'))
            if rec.state == 'dispatched':
                # Release vehicle and driver
                rec.vehicle_id.write({'status': 'available'})
                rec.driver_id.write({'status': 'on_duty'})
            rec.write({'state': 'cancelled'})

    def action_reset_draft(self):
        for rec in self:
            if rec.state != 'cancelled':
                raise UserError(_('Only cancelled trips can be reset to draft.'))
            rec.write({'state': 'draft'})
