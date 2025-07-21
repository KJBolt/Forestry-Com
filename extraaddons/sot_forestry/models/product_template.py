from odoo import api, fields, models

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    volume_uom_id = fields.Many2one('uom.uom', string='Volume UoM', help='Unit of Measure for Volume')

    # will be used to calculate Volume/Qty using formula
    formula_id = fields.Many2one('formula.formula', string="Product Type", tracking=True)
    formula_html = fields.Html(string="Formula Preview", related='formula_id.formula_html', readonly=True)

    tif_formula_id = fields.Many2one('formula.formula', string="TIF Details", tracking=True)
    tif_formula_html = fields.Html(string="TIF Formula Preview", related='tif_formula_id.formula_html', readonly=True)