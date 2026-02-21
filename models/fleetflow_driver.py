# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date


class FleetflowDriver(models.Model):
    _name = 'fleetflow.driver'
    _description = 'FleetFlow Driver Profile'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc'

    name = fields.Char(string='Driver Name', required=True, tracking=True)
    employee_id = fields.Char(string='Employee ID', copy=False)
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')

    # License
    license_number = fields.Char(string='License Number', required=True, tracking=True)
    license_category = fields.Selection([
        ('truck', 'Truck'),
        ('van', 'Van'),
        ('bike', 'Bike'),
        ('all', 'All Categories'),
    ], string='License Category', required=True, default='van', tracking=True)
    license_expiry = fields.Date(string='License Expiry Date', required=True, tracking=True)
    license_valid = fields.Boolean(
        string='License Valid',
        compute='_compute_license_valid',
        store=True,
    )
    days_to_expiry = fields.Integer(
        string='Days to Expiry',
        compute='_compute_license_valid',
        store=True,
    )

    # Status
    status = fields.Selection([
        ('on_duty', 'On Duty'),
        ('off_duty', 'Off Duty'),
        ('on_trip', 'On Trip'),
        ('suspended', 'Suspended'),
    ], string='Status', default='off_duty', required=True, tracking=True)

    # Performance
    safety_score = fields.Float(
        string='Safety Score',
        default=100.0,
        help='Safety score out of 100',
        tracking=True,
    )
    total_trips = fields.Integer(string='Total Trips', compute='_compute_performance', store=True)
    completed_trips = fields.Integer(string='Completed Trips', compute='_compute_performance', store=True)
    completion_rate = fields.Float(string='Completion Rate (%)', compute='_compute_performance', store=True)

    trip_ids = fields.One2many('fleetflow.trip', 'driver_id', string='Trips')

    @api.depends('license_expiry')
    def _compute_license_valid(self):
        today = date.today()
        for rec in self:
            if rec.license_expiry:
                delta = (rec.license_expiry - today).days
                rec.days_to_expiry = delta
                rec.license_valid = delta >= 0
            else:
                rec.days_to_expiry = 0
                rec.license_valid = False

    @api.depends('trip_ids.state')
    def _compute_performance(self):
        for rec in self:
            all_trips = rec.trip_ids.filtered(lambda t: t.state not in ['draft', 'cancelled'])
            completed = rec.trip_ids.filtered(lambda t: t.state == 'completed')
            rec.total_trips = len(all_trips)
            rec.completed_trips = len(completed)
            rec.completion_rate = (len(completed) / len(all_trips) * 100) if all_trips else 0.0

    def is_available_for_vehicle(self, vehicle_type):
        """Check if driver can be assigned to a vehicle of given type."""
        if not self.license_valid:
            return False, _('Driver license is expired or invalid.')
        if self.status in ('suspended', 'on_trip'):
            return False, _('Driver is not available (status: %s).') % self.status
        if self.license_category != 'all' and self.license_category != vehicle_type:
            return False, _('Driver license category (%s) does not match vehicle type (%s).') % (
                self.license_category, vehicle_type)
        return True, ''

    def action_set_on_duty(self):
        self.write({'status': 'on_duty'})

    def action_set_off_duty(self):
        self.write({'status': 'off_duty'})

    def action_suspend(self):
        self.write({'status': 'suspended'})
