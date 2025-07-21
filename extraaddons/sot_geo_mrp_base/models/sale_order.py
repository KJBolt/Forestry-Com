from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    phone = fields.Char(string='Phone', related='partner_id.phone', readonly=False)
    email = fields.Char(string='Email', related='partner_id.email', readonly=False)
    production_order_ids = fields.One2many(
        'mrp.production.batch', 'sale_order_id', string='Manufacturing Orders'
    )
    direct_mrp_production_count = fields.Integer(compute='_compute_direct_mrp_production_count')
    active_mrp_production_count = fields.Integer(compute='_compute_direct_mrp_production_count')

    def _compute_direct_mrp_production_count(self):
        for rec in self:
            rec.direct_mrp_production_count = len(rec.production_order_ids)
            rec.active_mrp_production_count = len(rec.production_order_ids.filtered(lambda x: x.state != 'cancel'))

    def action_view_direct_mrp_production(self):
        self.ensure_one()

        if len(self.production_order_ids) > 1:
            return {
                'name': 'Manufacturing Orders',
                'type': 'ir.actions.act_window',
                'res_model': 'mrp.production.batch',
                'view_mode': 'tree,form',
                'context': {'default_sale_order_id': self.id, 'default_source_type': 'sale_order'},
                'domain': [('id', 'in', self.production_order_ids.ids)],
            }

        return {
            'name': 'Manufacturing Order',
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production.batch',
            'view_mode': 'form',
            'view_type': 'form',
            'context': {'default_sale_order_id': self.id, 'default_source_type': 'sale_order'},
            'res_id': self.production_order_ids.id,
        }


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    volume_qty = fields.Float(string='Volume')
    product_volume_uom_category_id = fields.Many2one(
        related='product_id.volume_uom_id.category_id',
        depends=['product_id']
    )
    volume_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string="Volume UoM",
        compute='_compute_product_volume_uom',
        store=True, readonly=False, precompute=True, ondelete='restrict',
        domain="[('category_id', '=', product_volume_uom_category_id)]"
    )

    @api.depends('product_id')
    def _compute_product_volume_uom(self):
        for line in self:
            if not line.volume_uom_id or (line.product_id.volume_uom_id.id != line.volume_uom_id.id):
                line.volume_uom_id = line.product_id.volume_uom_id
