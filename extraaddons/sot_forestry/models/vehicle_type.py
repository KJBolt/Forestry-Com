from odoo import fields, models


class VehicleType(models.Model):
    _name = 'vehicle.type'
    _description = 'Forest Type'
    _order = 'id desc'

    active = fields.Boolean(string="Active", default=True)
    name = fields.Char(string="Name", required=True)
    sequence = fields.Integer(string="Sequence", default=10, index=True)
    note = fields.Text(string="Note")
