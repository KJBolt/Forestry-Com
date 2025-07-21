from odoo import fields, models


class ForestType(models.Model):
    _name = 'forest.type'
    _description = 'Forest Type'
    _order = 'id desc'

    active = fields.Boolean(string="Active", default=True)
    name = fields.Char(string="Name", required=True)
    sequence = fields.Integer(string="Sequence", default=10, index=True)
    note = fields.Text(string="Note")
