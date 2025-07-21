from odoo import api, fields, models


class WorkOrderArea(models.Model):
    _name = "mrp.workorder.area"
    _description = "Work Center Area"

    name = fields.Char(string="Area Name", required=True)
    code = fields.Char(string="Area Code", required=True)
    description = fields.Text(string="Description")
    active = fields.Boolean(string="Active", default=True)
    note = fields.Text(string="Remark")


class MrpWorkOrder(models.Model):
    _inherit = 'mrp.workorder'

    name = fields.Char(string="Work Order", related='operation_id.name')
    shift_id = fields.Many2one('mrp.workcenter.shift', string="Shift")
    req_area_id = fields.Many2one('mrp.workorder.area', string="Req. Area")
