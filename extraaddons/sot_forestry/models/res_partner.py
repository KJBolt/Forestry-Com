from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    customer_type = fields.Selection([
        ('customer', 'Customer'),
        ('supplier', 'Supplier'),
        ('range_supervisor', 'Range Supervisor'),
        ('driver', 'Driver'),
    ], 'Contact Type', index=True, copy=False, tracking=True)
