import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ForestTreeInformation(models.Model):
    _name = "forest.tree.information"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Forest Tree Information"
    _order = 'id desc'

    active = fields.Boolean(string="Active", default=True)
    note = fields.Text(string="Note")
    name = fields.Char(string="Serial No", required=True, default=lambda self: _("New"), tracking=True, readonly=True)
    forest_reverse_id = fields.Many2one("forest.reverse", string="Forest Name")
    plot_compartment_id = fields.Many2one('forest.reverse.line', string="Plot/Compartment")
    range_supervisor_id = fields.Many2one('res.partner', string='Range Supervisor')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    supplier_id = fields.Many2one('res.partner', string="Supplier Name", domain=[('customer_type', '=', 'supplier')])
    operator_id = fields.Many2one('res.users', string="Forestry Coordinator")
    tif_no = fields.Char(string="TIF No")
    tif_date = fields.Date(string="TIF Date")
    document_date = fields.Date(string="Document Date")
    remarks = fields.Text(string="Remarks")
    information_line_ids = fields.One2many(
        'forest.tree.inforamtion.line', 'forest_information_id',
        string="Forest Information Line"
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('cancel', 'Canceled')],
        default='draft',
        string="Status",
        tracking=True,
    )

    @api.onchange('forest_reverse_id')
    def get_forest_reverse_id(self):
        if self.forest_reverse_id:
            plot_compartment_id = self.env['forest.reverse.line'].search(
                [('reverse_id', '=', self.forest_reverse_id.id)], limit=1)
            if plot_compartment_id:
                self.plot_compartment_id = plot_compartment_id.id
            else:
                self.plot_compartment_id = False
        else:
            self.plot_compartment_id = False

    @api.constrains('information_line_ids')
    def _check_information_line_ids(self):
        for rec in self:
            if not rec.information_line_ids:
                raise ValidationError(_("Please add tree details."))

            line_set = set(rec.information_line_ids.mapped('tree_id'))
            if len(line_set) != len(rec.information_line_ids):
                raise ValidationError(_("Tree number must be unique."))

    def action_approve(self):
        for rec in self:
            rec.write({'state': 'approved'})

    def action_cancel(self):
        for rec in self:
            rec.write({'state': 'cancel'})

    def action_reset_draft(self):
        for rec in self:
            rec.write({'state': 'draft'})

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('forest.tree.information')
        result = super(ForestTreeInformation, self).create(vals)
        return result


class ForestInformationLine(models.Model):
    _name = "forest.tree.inforamtion.line"
    _description = "Tree Information Line"

    def _default_uom(self):
        uom = self.env.ref('uom.product_uom_cubic_meter', raise_if_not_found=False)
        return uom.id

    tree_id = fields.Many2one("forest.tree.line", string="Stock Number")
    contr_tree_no = fields.Char(string="Contractor Tree No", help="Contractor Tree No")

    product_id = fields.Many2one(
        "product.product", related="tree_id.product_id",
        string="Species", help="Product with species attribute"
    )
    species_id = fields.Many2one("product.attribute.value", related="tree_id.species_id", string="Species", )

    # Calculate Volume/Qty using formula
    formula_id = fields.Many2one('formula.formula', string="Product Type", tracking=True)
    formula_html = fields.Html(string="Formula Preview", related='formula_id.formula_html', readonly=True)
    formula_text = fields.Text(string="Formula Text", related='formula_id.formula', readonly=True)
    formula_variables = fields.Json(string='Formula Variables', related='formula_id.variables')
    formula_values = fields.Json(string='Formula Values')
    quantity = fields.Float(string="Volume", digits='Volume')

    # Calculate Volume/Qty using formula
    tif_formula_id = fields.Many2one('formula.formula', string="TIF Details", tracking=True)
    tif_formula_html = fields.Html(string="TIF Formula Preview", related='tif_formula_id.formula_html', readonly=True)
    tif_formula_text = fields.Text(string="TIF Formula Text", related='tif_formula_id.formula', readonly=True)
    tif_formula_variables = fields.Json(string='TIF Formula Variables', related='tif_formula_id.variables')
    tif_formula_values = fields.Json(string='TIF Formula Values')
    tif_quantity = fields.Float(string="TIF Volume", digits='Volume')

    unit_id = fields.Many2one("uom.uom", string="Unit", default=_default_uom)
    variance = fields.Float(string="Variance", digits='Volume', compute='_compute_variance', store=True)
    forest_information_id = fields.Many2one('forest.tree.information', string="Forest Information")

    @api.depends('tif_quantity', 'quantity')
    def _compute_variance(self):
        for record in self:
            record.variance = record.tif_quantity - record.quantity

    @api.onchange('product_id', 'tree_id')
    def _onchange_product_set_formula(self):
        if self.product_id:
            self.formula_id = self.product_id.product_tmpl_id.formula_id.id
            self.tif_formula_id = self.product_id.product_tmpl_id.tif_formula_id.id
            self.formula_values = {}
            self.tif_formula_values = {}
            self.quantity = 0
            self.tif_quantity = 0

        tree_felling_line_id = self.env['forest.tree.felling.line'].search([
            ('tree_id', '=', self.tree_id.id), ('forest_felling_id.state', '=', 'approved')
        ])
        if tree_felling_line_id:
            tree_felling_line_id = tree_felling_line_id[0]
            self.contr_tree_no = tree_felling_line_id.contr_tree_no
            self.formula_id = tree_felling_line_id.formula_id.id
            self.formula_values = tree_felling_line_id.formula_values
            self.quantity = tree_felling_line_id.quantity
