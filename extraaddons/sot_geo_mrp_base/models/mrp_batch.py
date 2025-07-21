import logging

from odoo import api, fields, models, Command, _

_logger = logging.getLogger(__name__)


class ProductionOrderType(models.Model):
    _name = "mrp.production.type"
    _description = "Production Order Type"

    name = fields.Char(string="Name", required=True)
    active = fields.Boolean(string="Active", default=True)


class BatchManufacturingOrder(models.Model):
    _name = "mrp.production.batch"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Production Order"
    _order = 'id desc, order_date desc'

    name = fields.Char(string="Serial No", default=lambda self: _("New"), tracking=True, readonly=True)
    active = fields.Boolean(string="Active", default=True)

    order_date = fields.Date(string="Order Date", default=fields.Date.today)
    order_type_id = fields.Many2one('mrp.production.type', string="Order Type")
    source_type = fields.Selection([
        ('manual', 'Manual'),
        # ('sale_order', 'Sales Order'),
        ('contract', 'Contract')
        ],
        default='manual',
        string="Source Type",
        tracking=True,
    )
    contract_ref = fields.Many2one('mrp.contract', string="Contract Reference")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)
    sale_order_id = fields.Many2one('sale.order', string="Sales Order")
    partner_id = fields.Many2one('res.partner', string="Customer", related='sale_order_id.partner_id', store=True)
    phone = fields.Char(string="Phone", related='partner_id.phone',store=True)
    email = fields.Char(string="Email", related='partner_id.email', store=True)
    commitment_date = fields.Date(string="Delivery Date")
    

    note = fields.Text(string="Remark")
    mo_ids = fields.One2many('mrp.production', 'mrp_batch_id', string="Operations")
    production_count = fields.Integer(compute='_compute_production_count')
    group_id = fields.Many2one('procurement.group', string="Group")

    order_line_ids = fields.One2many('mrp.production.batch.line', 'order_id', string="Finish Goods")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('cancel', 'Canceled'),
        ('close', 'Closed')
    ], default='draft', string="Status", tracking=True)

    @api.onchange('contract_ref')
    def onchange_contract_ref(self):
        for rec in self:
            if rec.contract_ref:
                rec.order_date = rec.contract_ref.date
                rec.partner_id = rec.contract_ref.buyer_name
                rec.commitment_date = rec.contract_ref.delivery_end_date
                rec.phone = rec.contract_ref.phone_no
                rec.email = rec.contract_ref.email
                order_lines = [Command.clear()]
                for line in rec.contract_ref.products:
                    order_lines.append((0, 0, {
                        'product_id': line.id,
                        'product_qty': line.qty_available,
                        'volume_qty': line.volume,
                        'volume_uom_id': line.volume_uom_id.id,
                    }))
                rec.order_line_ids = order_lines




    @api.depends_context('default_sale_order_id', 'sale_order_id')
    @api.onchange('sale_order_id')
    def _onchange_sale_order_id(self):
        for rec in self:
            rec.order_date = rec.sale_order_id.date_order
            rec.commitment_date = rec.sale_order_id.commitment_date
            rec.partner_id = rec.sale_order_id.partner_id
            order_lines = [Command.clear()]
            for line in rec.sale_order_id.order_line:
                order_lines.append(Command.create({
                    'product_id': line.product_id.id,
                    'product_qty': line.product_uom_qty,
                    'volume_qty': line.volume_qty,
                    'uom_id': line.product_uom.id,
                    'volume_uom_id': line.volume_uom_id.id,
                    'sale_line_id': line.id,
                }))

            rec.order_line_ids = order_lines

    @api.depends('mo_ids')
    def _compute_production_count(self):
        for rec in self:
            rec.production_count = len(rec.mo_ids)

    def action_approve(self):
        for rec in self:
            rec.write({'state': 'approved'})

    def action_cancel(self):
        for rec in self:
            rec.write({'state': 'cancel'})

    def action_reset_draft(self):
        for rec in self:
            rec.write({'state': 'draft'})

    def action_close(self):
        for rec in self:
            rec.write({'state': 'close'})

    def _prepare_procurement_group(self):
        return {
            'name': self.name,
            'move_type': 'direct',
        }

    def action_view_direct_sale_orders(self):
        self.ensure_one()

        if not self.sale_order_id:
            return

        return {
            'name': 'Sale Orders',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.sale_order_id.id,
        }

    def action_view_mrp_production(self):
        self.ensure_one()

        default_context = {
            'default_mrp_batch_id': self.id,
            'default_origin': self.name,
            'create': self.state != 'close',
            'write': self.state != 'close',
            'duplicate': self.state != 'close',
            'delete': self.state != 'close',
        }

        if len(self.mo_ids) == 1:
            return {
                'name': 'Job Executions',
                'type': 'ir.actions.act_window',
                'res_model': 'mrp.production',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': self.mo_ids.id,
                'context': default_context,
                'domain': [('mrp_batch_id', 'in', self.ids)],
            }

        return {
            'name': 'Job Executions',
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'tree,form',
            'context': default_context,
            'domain': [('mrp_batch_id', 'in', self.ids)],
        }

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('mrp.production.batch')
        result = super(BatchManufacturingOrder, self).create(vals)
        result.group_id = self.env['procurement.group'].create(result._prepare_procurement_group()).id
        return result


class ProductionOrderLine(models.Model):
    _name = 'mrp.production.batch.line'
    _description = 'Production Order Line'

    order_id = fields.Many2one('mrp.production.batch', string="Batch Order")
    product_id = fields.Many2one('product.product', string="Product")
    product_qty = fields.Float(string="Quantity")
    uom_id = fields.Many2one('uom.uom', string="UoM")
    volume_qty = fields.Float(string="Volume")
    volume_uom_id = fields.Many2one('uom.uom', string="Volume UoM")
    sale_line_id = fields.Many2one('sale.order.line', string="Sale Order Line")
    note = fields.Text(string="Remark")
