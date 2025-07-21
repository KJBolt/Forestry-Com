import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import frozendict

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    forest_id = fields.Many2one('forest.reverse', string='Forest')
    plot_id = fields.Many2one('forest.reverse.line', string='Plot/Compartment')
    waybill_id = fields.Many2one('waybill.waybill', string='Waybill')
    is_forest_order = fields.Boolean(string='Is Forest Order')
    scheduled_date = fields.Datetime(string='Document Date')

