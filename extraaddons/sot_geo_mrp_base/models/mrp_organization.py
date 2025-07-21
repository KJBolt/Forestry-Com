import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ManufacturingOrganization(models.Model):
    _name = "mrp.production.org"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Production Organization"

    name = fields.Char(string="Name", tracking=True)
    production_id = fields.Many2one('mrp.production', string="Production Order")
    active = fields.Boolean(string="Active", default=True)
