from odoo import fields, models, api
from odoo.tools.translate import _


class PriceListApproval(models.Model):
    _name = "forest.pricelist.approval"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Forest PriceList Approval"
    _order = "effective_date desc"

    active = fields.Boolean(string="Active", default=True)

    name = fields.Char(string="Name", default=lambda self: _("New"), tracking=True)
    forest_type_id = fields.Many2one("forest.type", string="Forest Type")
    forest_reverse_id = fields.Many2one("forest.reverse", string="Forest Name")
    plot_compartment_id = fields.Many2one('forest.reverse.line', string="Plot/Compartment")
    product_id = fields.Many2one(
        "product.product",
        string="Product",
    )
    uom_id = fields.Many2one("uom.uom", string="UoM")
    approved_price = fields.Float(string="Price", digits='Product Price', )
    effective_date = fields.Date(string="Effective From")
    note = fields.Text(string="Note")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('cancel', 'Canceled')],
        default='draft',
        string="Status",
        tracking=True,
    )

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('product.pricelist.sequence') or '/'
        return super(PriceListApproval, self).create(vals)

    def action_approve(self):
        for rec in self:
            rec.write({'state': 'approved'})

    def action_cancel(self):
        for rec in self:
            rec.write({'state': 'cancel'})

    def action_reset_draft(self):
        for rec in self:
            rec.write({'state': 'draft'})
