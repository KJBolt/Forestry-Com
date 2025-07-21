import logging

from odoo import api, fields, models, _, Command

_logger = logging.getLogger(__name__)


class WorkCenter(models.Model):
    _inherit = "mrp.workcenter"

    description = fields.Char(string="Description", tracking=True)
    product_ids = fields.Many2many("product.product", string="Allowed Products")

    shift_ids = fields.One2many('mrp.workcenter.shift', 'workcenter_id', string="Shifts")
    manpower_ids = fields.One2many('mrp.workcenter.manpower', 'workcenter_id', string="Manpower")

    @api.onchange('resource_calendar_id')
    def _onchange_resource_calendar_id(self):
        self.shift_ids = [Command.clear()]

        if self.resource_calendar_id:
            shift_commands = []
            for attendance in self.resource_calendar_id.attendance_ids:
                shift_commands.append(Command.create({
                    'name': attendance.name,
                    'dayofweek': attendance.dayofweek,
                    'day_period': attendance.day_period,
                    'start_time': attendance.hour_from,
                    'end_time': attendance.hour_to,
                    'duration_days': attendance.hour_to - attendance.hour_from,
                }))
            self.shift_ids = shift_commands


class RoutingWorkCenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    organization_ids = fields.One2many('mrp.production.org', 'production_id', string="Organization")


class WorkCenterShifts(models.Model):
    _name = "mrp.workcenter.shift"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Work Center Shifts"

    name = fields.Char(string="Shift Name")
    dayofweek = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], 'Day of Week', required=True, index=True, default='0')
    start_time = fields.Float(string="Start Time")
    end_time = fields.Float(string="End Time")
    day_period = fields.Selection([
        ('morning', 'Morning'),
        ('lunch', 'Break'),
        ('afternoon', 'Afternoon')], required=True, default='morning')
    duration_days = fields.Float(string='Duration (days)', store=True, readonly=False)

    workcenter_id = fields.Many2one("mrp.workcenter", string="Shift")
    sequence = fields.Integer(string="Sequence", default=10, index=True)

    active = fields.Boolean(string="Active", default=True)
    default_shift = fields.Boolean(string="Default Shift")
    note = fields.Text(string="Remark")


class WorkCenterManpower(models.Model):
    _name = "mrp.workcenter.manpower"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Manpower for Work Center"

    employee_id = fields.Many2one('hr.employee', string='Employee', tracking=True)
    name = fields.Char(string="Shift Name")
    dayofweek = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], 'Day of Week', required=True, index=True, default='0')
    start_time = fields.Float(string="Start Time")
    end_time = fields.Float(string="End Time")
    day_period = fields.Selection([
        ('morning', 'Morning'),
        ('lunch', 'Break'),
        ('afternoon', 'Afternoon')], required=True, default='morning')
    workcenter_id = fields.Many2one("mrp.workcenter", string="Shift")
    sequence = fields.Integer(string="Sequence", default=10, index=True)
    duration_days = fields.Float(string='Duration (days)', store=True, readonly=False)
    effective_date = fields.Date(string="Effective Date")
    active = fields.Boolean(string="Employee Active", default=True)
    default_employee = fields.Boolean(string="Default Employee")
    note = fields.Text(string="Remark")

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id and self.employee_id.resource_calendar_id.attendance_ids:
            attendance = self.employee_id.resource_calendar_id.attendance_ids[0]

            self.name = attendance.name
            self.dayofweek = attendance.dayofweek
            self.day_period = attendance.day_period
            self.start_time = attendance.hour_from
            self.end_time = attendance.hour_to
            self.duration_days = attendance.hour_to - attendance.hour_from
        else:
            self.name = False
            self.dayofweek = False
            self.day_period = False
            self.start_time = False
            self.end_time = False
            self.duration_days = False
