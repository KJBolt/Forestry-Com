import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    # Calculate Volume/Qty using formula
    formula_id = fields.Many2one('formula.formula', string="Product Type", tracking=True)
    formula_html = fields.Html(string="Formula Preview", related='formula_id.formula_html', readonly=True)
    formula_text = fields.Text(string="Formula Text", related='formula_id.formula', readonly=True)
    formula_variables = fields.Json(string='Formula Variables', related='formula_id.variables')
    formula_values = fields.Json(string='Formula Values')
    volume = fields.Float(string="Volume", digits='Volume')
    volume_uom_id = fields.Many2one('uom.uom', related='product_id.volume_uom_id')

    @api.model
    def _get_inventory_fields_write(self):
        """ Returns a list of fields user can edit when he wants to edit a quant in `inventory_mode`."""
        inventory_fields = super()._get_inventory_fields_write() or []
        return inventory_fields + ['formula_id', 'formula_values', 'volume']

    @api.model_create_multi
    def create(self, vals_list):
        quants = super(StockQuant, self).create(vals_list)
        pickings = self.env.context.get('button_validate_picking_ids')

        if pickings:
            move_line_ids = self.env['stock.move.line'].search([('picking_id', 'in', pickings)])
            for move_line in move_line_ids:
                matched_quant = quants.filtered(
                    lambda q: q.product_id == move_line.product_id and q.location_id in [
                        move_line.location_id,
                        move_line.location_dest_id
                    ]
                )
                for matched_quant_id in matched_quant:
                    update_values = move_line._prepare_stock_quant_volume_vals(matched_quant_id)
                    matched_quant.update(update_values)

        return quants
