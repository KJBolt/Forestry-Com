import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ForestTreeFelling(models.Model):
    _name = "forest.tree.felling"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Forest Tree Felling"
    _order = 'id desc'

    active = fields.Boolean(string="Active", default=True)
    note = fields.Text(string="Note")
    name = fields.Char(string="Serial No", required=True, default=lambda self: _("New"), tracking=True, readonly=True)
    forest_reverse_id = fields.Many2one("forest.reverse", string="Forest Name")
    plot_compartment_id = fields.Many2one('forest.reverse.line', string="Plot/Compartment")
    machine_id = fields.Many2one('machine.machine', string="Machine Name")
    operator_id = fields.Many2one('res.users', string="Operator Name")
    machine_run_time = fields.Char(string="Machine Run Time")
    tree_fell_date = fields.Date(string="Tree Fell Date")
    remarks = fields.Text(string="Remarks")
    felling_line_ids = fields.One2many('forest.tree.felling.line', 'forest_felling_id', string="Forest Felling Line")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('cancel', 'Canceled')],
        default='draft',
        string="Status",
        tracking=True,
    )
    reset_count = fields.Integer(string="Reset Count", default=0)

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

    @api.constrains('felling_line_ids')
    def _check_felling_line_ids(self):
        for rec in self:
            if not rec.felling_line_ids:
                raise ValidationError(_("Please add tree details."))

            tree_set = set(rec.felling_line_ids.mapped('tree_id'))
            if len(tree_set) != len(rec.felling_line_ids):
                raise ValidationError(_("You can't select same tree multiple times."))

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('forest.tree.felling')
        result = super(ForestTreeFelling, self).create(vals)
        return result

    def action_approve(self):
        for rec in self:
            fallen_trees = rec.felling_line_ids.filtered(
                lambda x: x.tree_id.state == 'fallen' and x.forest_felling_id != rec)
            if fallen_trees:
                raise ValidationError(
                    _("The following trees are already fallen: \n%s\n\nPlease remove them to approve!" % fallen_trees.mapped(
                        'tree_id.name')))

            rec.felling_line_ids.mapped('tree_id').write({'state': 'fallen'})
            rec.write({'state': 'approved'})

    def action_cancel(self):
        for rec in self:
            rec.felling_line_ids.mapped('tree_id').write({'state': 'standing'})
            rec.write({'state': 'cancel'})

    def action_reset_draft(self):
        for rec in self:
            rec.reset_count += 1
            rec.name = f"{rec.name.split('/')[0]}/{rec.reset_count}"
            rec.write({'state': 'draft'})


class ForestFellingLine(models.Model):
    _name = "forest.tree.felling.line"
    _description = "Tree Felling Line"

    def _default_uom(self):
        uom = self.env.ref('uom.product_uom_cubic_meter', raise_if_not_found=False)
        return uom.id

    tree_id = fields.Many2one("forest.tree.line", string="Stock Number")
    contr_tree_no = fields.Char(string="Contractor Tree No", help="Contractor Tree No")
    diameter = fields.Integer(string="Diameter", related="tree_id.diameter", store=True)
    product_id = fields.Many2one(
        "product.product", related="tree_id.product_id",
        string="Species", help="Product with species attribute"
    )
    species_id = fields.Many2one("product.attribute.value", related="tree_id.species_id", string="Species", )
    defect_id = fields.Many2one(
        "account.analytic.account",
        string="Defect",
    )
    unit_id = fields.Many2one("uom.uom", string="Unit", default=_default_uom)
    remarks = fields.Text(string="Remarks")
    forest_felling_id = fields.Many2one('forest.tree.felling', string="Forest Felling")

    # Calculate Volume/Qty using formula
    formula_id = fields.Many2one('formula.formula', string="Product Type", tracking=True)
    formula_html = fields.Html(string="Formula Preview", related='formula_id.formula_html', readonly=True)
    formula_text = fields.Text(string="Formula Text", related='formula_id.formula', readonly=True)
    formula_variables = fields.Json(string='Formula Variables', related='formula_id.variables')
    formula_values = fields.Json(string='Formula Values')
    # quantity = fields.Float(string="Volume", digits='Volume')
    quantity = fields.Float(string="Volume", digits=(16, 3))  # Changed from digits='Volume' to (16,3)

    @api.onchange('product_id', 'tree_id')
    def _onchange_product_set_formula(self):
        if self.product_id:
            self.formula_id = self.product_id.product_tmpl_id.formula_id.id
            self.formula_values = {}
