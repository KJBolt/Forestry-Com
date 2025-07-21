from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    forest_id = fields.Many2one('forest.reverse', string='Forest')
    plot_id = fields.Many2one('forest.reverse.line', string='Plot/Compartment')
    waybill_id = fields.Many2one('waybill.waybill', string='Waybill')
    is_forest_order = fields.Boolean(string='Is Forest Order')

    def _prepare_picking(self):
        values = super(PurchaseOrder, self)._prepare_picking()
        values['plot_id'] = self.plot_id.id
        values['forest_id'] = self.forest_id.id
        values['waybill_id'] = self.waybill_id.id
        values['is_forest_order'] = self.is_forest_order
        return values



class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    species_id = fields.Many2one('product.product', string='Species')
    tree_id = fields.Many2one("forest.tree.line", string="Stock Number")
    log_id = fields.Many2one('cross.cut.log.line', string="Cross Cut Log No", help="Cross Cut Log Number")
    grading = fields.Char(string='Grading')
    contr_tree_no = fields.Char(string="Contract Tree No", help="Contract Tree No")
    diameter = fields.Float(string="Diameter", related="tree_id.diameter")
    remarks = fields.Text(string='Remarks')

    # Calculate Volume/Qty using formula
    formula_id = fields.Many2one('formula.formula', string="Product Type", tracking=True)
    formula_html = fields.Html(string="Formula Preview", related='formula_id.formula_html', readonly=True)
    formula_text = fields.Text(string="Formula Text", related='formula_id.formula', readonly=True)
    formula_variables = fields.Json(string='Formula Variables', related='formula_id.variables')
    formula_values = fields.Json(string='Formula Values')
    volume = fields.Float(string="Volume", digits='Volume')

    @api.onchange('product_id')
    def _onchange_product_set_formula(self):
        if self.product_id:
            self.formula_id = self.product_id.product_tmpl_id.formula_id.id
            self.formula_values = {}

    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        values = super(PurchaseOrderLine, self)._prepare_stock_move_vals(
            picking, price_unit, product_uom_qty, product_uom
        )

        values['formula_id'] = self.formula_id.id
        values['formula_values'] = self.formula_values
        values['volume'] = self.volume
        values['remarks'] = self.remarks

        return values

    
