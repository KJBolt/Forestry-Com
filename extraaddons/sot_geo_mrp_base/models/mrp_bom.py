from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.exceptions import ValidationError

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    valid_form = fields.Date(string="Valid Form")
    valid_to = fields.Date(string="Valid To")
    list_of_item_group = fields.Char(string="List Of Item Group", tracking=True)
    requirement_area = fields.Char(string="Requirement Area")
    note = fields.Text(string="Remark")

    formula_type = fields.Selection([
        ('random_size', 'Random Size'),
        ('fixed_size', 'Fixed Size'),
    ], string="Formula Type", default='fixed_size')
    formula_id = fields.Many2one('formula.formula', string="Formula", tracking=True)
    formula_text = fields.Text(string="Formula Text", related='formula_id.formula')
    formula_html = fields.Html(string="Formula Preview", related='formula_id.formula_html')
    validate_quantity = fields.Boolean(string="Validate Volume?", default=True)

    @api.constrains('valid_form', 'valid_to')
    def _check_valid_form_to(self):
        for rec in self:
            if rec.valid_form and rec.valid_to and rec.valid_form > rec.valid_to:
                raise ValueError("Valid Form must be less than Valid To.")

    @api.constrains('active', 'product_id', 'product_tmpl_id', 'bom_line_ids')
    def _check_bom_cycle(self):
        allow_bom_cycle = self.env['ir.config_parameter'].sudo().get_param('sot_geo_mrp_base.allow_bom_cycle')
        if not allow_bom_cycle:
            super()._check_bom_cycle()

        return False

    @api.constrains('bom_line_ids')
    def _check_unique_raw_materials(self):
        for bom in self:
            if len(bom.bom_line_ids) > len(set(bom.bom_line_ids.mapped('product_id'))):
                raise ValidationError(
                    _('The same product can not be used multiple times in the same bill of materials.')
                )

        return True
