import logging

from odoo import api, fields, models, _, Command
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class WayBill(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'waybill.waybill'
    _description = 'Waybill'
    _order = 'id desc'

    name = fields.Char(string="Serial No", required=True, default=lambda self: _("New"), tracking=True, readonly=True)
    lif_number = fields.Char(string="LIF Number", tracking=True)
    lif_date = fields.Date(string='LIF Date', tracking=True)

    forest_id = fields.Many2one('forest.reverse', string='Forest', tracking=True)
    plot_id = fields.Many2one('forest.reverse.line', string='Plot/Compartment', tracking=True)
    manager_id = fields.Many2one('res.users', string='Manager', tracking=True)
    supplier_id = fields.Many2one('res.partner', string='Supplier', tracking=True, domain=[('customer_type', '=', 'supplier')])
    remarks = fields.Text(string='Remarks')

    lmcc_no = fields.Char(string='LMCC No', tracking=True)
    lmcc_date = fields.Date(string='LMCC Date', tracking=True)

    waybill_no = fields.Char(string='Waybill Number', default=lambda self: _("New"), tracking=True, readonly=True)
    waybill_date = fields.Date(string='Waybill Date', default=fields.Date.context_today, tracking=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', tracking=True)
    driver_id = fields.Many2one('res.partner', string='Driver', tracking=True)
    transport_type_id = fields.Many2one('vehicle.type', string='Vehicle Type', tracking=True)
    current_reading = fields.Float(string='Current Reading', tracking=True)
    cross_cut_log_id = fields.Many2one('cross.cut.log.line', string="Cross Cut Log Number", help="Cross Cut Log Number",tracking=True)
    log_line_ids = fields.Many2many('cross.cut.log.line', string='LIF Details', tracking=True)
    purchase_order_id = fields.Many2one("purchase.order", string="Purchase Order", tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('cancel', 'Canceled')],
        default='draft',
        string="Status",
        tracking=True,
    )
    product_id = fields.Many2one(
        "product.product", 
        related="cross_cut_log_id.product_id",
        string="Species", 
        help="Product with species attribute",
        store=True
    )

    @api.onchange('forest_id')
    def get_forest_id(self):
        if self.forest_id:
            plot_id = self.env['forest.reverse.line'].search([('reverse_id', '=', self.forest_id.id)], limit=1)
            if plot_id:
                self.plot_id = plot_id.id
            else:
                self.plot_id = False
        else:
            self.plot_id = False

    @api.onchange('cross_cut_log_id')
    def _onchange_cross_cut_log_id(self):
        if self.cross_cut_log_id:
            self.forest_id = self.cross_cut_log_id.log_id.forest_id.id
            self.log_line_ids = [Command.link(self.cross_cut_log_id.id)]
            self.cross_cut_log_id = False

    @api.constrains('log_line_ids')
    def _check_log_line_ids(self):
        for rec in self:
            if not rec.log_line_ids and rec.state != 'draft':
                raise ValidationError(_("Please add LIF details."))

            for line in rec.log_line_ids:
                if line.quantity < 0:
                    raise ValidationError(_("Quantity must be positive."))

    def action_approve(self):
        # Create Purchase Order
        po_vals = self._prepare_purchase_order_vals()
        _logger.info(f"po_vals: {po_vals}")
        purchase_order = self.env['purchase.order'].create(po_vals)
        self.purchase_order_id = purchase_order.id
        self.write({'state': 'approved'})

        # Prepare and create Purchase Order Lines
        for line in self.log_line_ids:
            po_line_vals = self._prepare_purchase_order_line(line, purchase_order)
            self.env['purchase.order.line'].create(po_line_vals)

        action = {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'res_id': purchase_order.id,
        }

        return action

    @api.model
    def _prepare_purchase_order_vals(self):
        return {
            'partner_id': self.supplier_id.id,
            'company_id': self.env.company.id,
            'forest_id': self.forest_id.id,
            'plot_id': self.plot_id.id,
            'waybill_id': self.id,
            'is_forest_order': True,
        }

    @api.model
    def _prepare_purchase_order_line(self, line, purchase_order):
        today = fields.Date.today()
        price_unit = self.env['forest.pricelist.approval'].search([
            ('product_id', '=', line.log_id.tree_id.species_id.id),
            ('plot_compartment_id', '=', self.plot_id.id),
            ('effective_date', '<=', today),
        ], limit=1, order='effective_date desc')
        tree_felling_line_id = self.env['forest.tree.felling.line'].search([
            ('forest_felling_id.state', '=', 'approved')
        ])

        contr_tree_no = False
        if tree_felling_line_id:
            tree_felling_line_id = tree_felling_line_id[0]
            contr_tree_no = tree_felling_line_id.contr_tree_no

        po_line_vals = {
            'order_id': purchase_order.id,
            'product_id': line.log_id.tree_id.product_id.id,
            'species_id': line.log_id.tree_id.species_id.id,
            'tree_id': line.log_id.tree_id.id,
            'log_id': line.id,
            'contr_tree_no': contr_tree_no,
            'diameter': line.log_id.tree_id.diameter,
            'formula_id': line.formula_id.id,
            'formula_values': line.formula_values,
            'volume': line.quantity,
            'price_unit': price_unit.approved_price if price_unit else 0.0,
        }
        return po_line_vals

    def action_view_purchase_order(self):
        return {
            'name': _('Purchase Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'res_id': self.purchase_order_id.id,
        }

    def action_cancel(self):
        for rec in self:
            rec.write({'state': 'cancel'})
            rec.purchase_order_id.button_cancel()

    def action_reset_draft(self):
        for rec in self:
            rec.write({'state': 'draft'})
            rec.purchase_order_id.unlink()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('waybill.lif.sequence') or _('New')
        vals['waybill_no'] = self.env['ir.sequence'].next_by_code('waybill.waybill.sequence') or _('New')
        return super(WayBill, self).create(vals)

    def action_print_pdf(self):
        return self.env.ref('sot_forestry.action_report_sot_forestry_waybill').report_action(self)
