import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    # Calculate Volume/Qty using formula
    formula_id = fields.Many2one('formula.formula', string="Product Type", tracking=True)
    formula_html = fields.Html(string="Formula Preview", related='formula_id.formula_html', readonly=True)
    formula_text = fields.Text(string="Formula Text", related='formula_id.formula', readonly=True)
    formula_variables = fields.Json(string='Formula Variables', related='formula_id.variables')
    formula_values = fields.Json(string='Formula Values')
    volume = fields.Float(string="Volume", digits='Volume')
    volume_done = fields.Float(string='Volume', compute='_compute_total_volume', digits='Volume')
    volume_uom_id = fields.Many2one('uom.uom', related='product_id.volume_uom_id')

    remarks = fields.Text(string='Remarks')

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        res = super(StockMove, self)._prepare_move_line_vals(quantity, reserved_quant)
        res.update({
            'remarks': self.remarks,
            'formula_id': self.formula_id.id or (reserved_quant and reserved_quant.formula_id.id),
            'formula_values': self.formula_values or (reserved_quant and reserved_quant.formula_values),
            'volume': self.volume or (reserved_quant and reserved_quant.volume),
        })
        return res

    @api.depends('move_line_ids')
    def _compute_total_volume(self):
        for rec in self:
            rec.volume_done = sum([x.volume for x in rec.move_line_ids])


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    formula_id = fields.Many2one('formula.formula', string="Product Type")
    formula_html = fields.Html(string="Formula Preview", related='formula_id.formula_html', readonly=True)
    formula_text = fields.Text(string="Formula Text", related='formula_id.formula', readonly=True)
    formula_variables = fields.Json(string='Formula Variables', related='formula_id.variables')
    formula_values = fields.Json(string='Formula Values')
    volume = fields.Float(string="Volume", digits='Volume')
    volume_uom_id = fields.Many2one('uom.uom', related='product_id.volume_uom_id')

    remarks = fields.Text(string='Remarks')

    def _prepare_stock_quant_volume_vals(self, quant_id):
        return {
            'formula_id': self.formula_id.id,
            'formula_values': self.formula_values,
            'volume': (self.volume * -1) if quant_id.quantity < 0 else self.volume,
        }

    @api.depends('quant_id')
    def _compute_quantity(self):
        for record in self:
            super()._compute_quantity()
            record.volume = record.quant_id.volume
            record.formula_id = record.quant_id.formula_id.id
            record.formula_values = record.quant_id.formula_values

        return True
