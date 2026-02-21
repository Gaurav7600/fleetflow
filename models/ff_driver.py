# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import date


class FleetFlowDriver(models.Model):
    _name = 'ff.driver'
    _description = 'FleetFlow Driver'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'name asc'

    name = fields.Char(string='Full Name', required=True, tracking=True)
    employee_id = fields.Char(string='Employee ID', copy=False)
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    photo = fields.Binary(string='Photo', attachment=True)

    license_number = fields.Char(string='License Number', required=True, copy=False)
    license_category = fields.Selection([
        ('truck', 'Truck'),
        ('van', 'Van'),
        ('bike', 'Bike'),
        ('all', 'All Categories'),
    ], string='License Category', required=True, default='van')
    license_expiry = fields.Date(string='License Expiry', required=True, tracking=True)
    license_expired = fields.Boolean(string='Expired', compute='_compute_license_status', store=True)
    days_to_expiry = fields.Integer(string='Days to Expiry', compute='_compute_license_status', store=True)

    state = fields.Selection([
        ('available', 'Available'),
        ('on_duty', 'On Duty'),
        ('off_duty', 'Off Duty'),
        ('suspended', 'Suspended'),
    ], string='Status', default='available', tracking=True, index=True)

    safety_score = fields.Float(string='Safety Score', default=100.0, digits=(16, 1), tracking=True)
    trip_completion_rate = fields.Float(string='Completion Rate (%)', compute='_compute_performance', store=True, digits=(16, 1))
    total_trips = fields.Integer(string='Total Trips', compute='_compute_performance', store=True)
    completed_trips = fields.Integer(string='Completed Trips', compute='_compute_performance', store=True)
    complaints = fields.Integer(string='Complaints', default=0)

    trip_ids = fields.One2many('ff.trip', 'driver_id', string='Trips')

    _sql_constraints = [
        ('license_number_uniq', 'UNIQUE(license_number)', 'License number must be unique!'),
    ]

    @api.depends('license_expiry')
    def _compute_license_status(self):
        today = date.today()
        for d in self:
            if d.license_expiry:
                delta = (d.license_expiry - today).days
                d.days_to_expiry = delta
                d.license_expired = delta < 0
            else:
                d.days_to_expiry = 0
                d.license_expired = True

    @api.depends('trip_ids', 'trip_ids.state')
    def _compute_performance(self):
        for d in self:
            all_t = d.trip_ids.filtered(lambda t: t.state != 'draft')
            done_t = all_t.filtered(lambda t: t.state == 'completed')
            d.total_trips = len(all_t)
            d.completed_trips = len(done_t)
            d.trip_completion_rate = (len(done_t) / len(all_t) * 100) if all_t else 0.0

    def _check_assignment_eligibility(self, vehicle_type=None):
        if self.license_expired:
            raise ValidationError(_('Driver "%s" has an expired license.') % self.name)
        if self.state == 'suspended':
            raise ValidationError(_('Driver "%s" is suspended.') % self.name)
        if self.state == 'on_duty':
            raise ValidationError(_('Driver "%s" is already on duty.') % self.name)
        if vehicle_type and self.license_category not in ('all', vehicle_type):
            raise ValidationError(_('Driver "%s" is not licensed for %s.') % (self.name, vehicle_type))

    def action_suspend(self):
        self.write({'state': 'suspended'})

    def action_reinstate(self):
        self.write({'state': 'available'})

    def action_set_off_duty(self):
        self.write({'state': 'off_duty'})

    def action_set_available(self):
        self.write({'state': 'available'})
