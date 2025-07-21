import logging
from collections import defaultdict
from datetime import date

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"
    _order = 'sequence asc, priority desc, date_start asc,id'

    sequence = fields.Integer(string="Sequence", default=10, index=True)
    bom_id = fields.Many2one(
        'mrp.bom', 'Bill of Material', readonly=False,
        domain=lambda self: [
            '&',
            '|',
            ('company_id', '=', False),
            ('company_id', '=', self.env.company.id),
            '&',
            '|',
            ('product_id', '=', self.product_id.id),
            '&',
            ('product_tmpl_id.product_variant_ids', '=', self.product_id.id),
            ('product_id', '=', False),
            ('type', '=', 'normal'),
            '&',
            ('valid_form', '<=', date.today()),
            '|',
            ('valid_to', '>=', date.today()),
            ('valid_to', '=', False),
        ],
        check_company=True, compute='_compute_bom_id', store=True, precompute=True,
        help="Bills of Materials, also called recipes, are used to autocomplete components and work order instructions."
    )

    organization_ids = fields.One2many(
        'mrp.production.org', 'production_id', string="Organization",
        domain=['|', ('active', '=', False), ('active', '=', True)], context={'active_test': False}
    )
    certification_status_id = fields.Many2one('certificate.status', string="Certification Status", required=True)

    mrp_batch_id = fields.Many2one('mrp.production.batch', string="Batch Order", copy=True)
    sale_order_id = fields.Many2one('sale.order', string="Sale Order", related='mrp_batch_id.sale_order_id', store=True)
    group_id = fields.Many2one('procurement.group', related='mrp_batch_id.group_id', string="Batch Group", store=True)
    note = fields.Text(string="Remarks")
    moisture_content = fields.Char(string="Moisture Content")
    issue_no = fields.Char(string="Issue No")
    receipt_no = fields.Char(string="Receipt No")
    contract_id = fields.Many2one(
        'mrp.contract',
        string="Contract Reference", 
        required=True
    )

    formula_type = fields.Selection([
        ('random_size', 'Random Size'),
        ('fixed_size', 'Fixed Size'),
    ], string="Formula Type", default='fixed_size')
    formula_id = fields.Many2one('formula.formula', string="Product Type", tracking=True)
    formula_html = fields.Html(string="Formula Preview", related='formula_id.formula_html')
    formula_text = fields.Text(string="Formula Text", related='formula_id.formula')
    formula_variables = fields.Json(string='Formula Variables', related='formula_id.variables')
    formula_values = fields.Json(string='Formula Values')
    validate_quantity = fields.Boolean(string="Validate Volume", default=False)
    formula_quantity = fields.Float(string="Volume", default=0.0, digits='Volume', tracking=True)

    product_volume_uom_category_id = fields.Many2one(
        related='product_id.volume_uom_id.category_id',
        depends=['product_id']
    )
    volume_unit = fields.Many2one(
        comodel_name='uom.uom',
        string="Volume UoM",
        compute='_compute_product_volume_uom',
        store=True, readonly=False, precompute=True, ondelete='restrict',
        domain="[('category_id', '=', product_volume_uom_category_id)]"
    )

    random_width_ids = fields.One2many(
        'mrp.random.formula.calculator',
        'production_id', string="Random Width",
        domain=[('value_type', '=', 'width')]
    )

    random_length_ids = fields.One2many(
        'mrp.random.formula.calculator',
        'production_id', string="Random Length",
        domain=[('value_type', '=', 'length')]
    )


    @api.depends('product_id')
    def _compute_bom_id(self):
        mo_by_company_id = defaultdict(lambda: self.env['mrp.production'])
        for mo in self:
            if not mo.product_id and not mo.bom_id:
                mo.bom_id = False
                continue
            mo_by_company_id[mo.company_id.id] |= mo

        for company_id, productions in mo_by_company_id.items():
            picking_type_id = self._context.get('default_picking_type_id')
            picking_type = picking_type_id and self.env['stock.picking.type'].browse(picking_type_id)
            boms_by_product = self.env['mrp.bom'].with_context(active_test=True)._bom_find(
                productions.product_id, picking_type=picking_type, company_id=company_id, bom_type='normal'
            )
            for production in productions:
                if not production.bom_id or production.bom_id.product_tmpl_id != production.product_tmpl_id or (
                        production.bom_id.product_id and production.bom_id.product_id != production.product_id
                ):
                    bom = boms_by_product[production.product_id]
                    production.bom_id = bom.id or False
                    self.env.add_to_compute(production._fields['picking_type_id'], production)

    @api.onchange('product_id', 'move_raw_ids')
    def _onchange_product_id(self):
        allow_bom_cycle = self.env['ir.config_parameter'].sudo().get_param('sot_geo_mrp_base.allow_bom_cycle')
        if not allow_bom_cycle:
            super()._onchange_product_id()

        return False

    @api.depends('product_id')
    def _compute_product_volume_uom(self):
        for line in self:
            if not line.volume_unit or (line.product_id.volume_uom_id.id != line.volume_unit.id):
                line.volume_unit = line.product_id.volume_uom_id

    @api.depends('bom_id')
    def _compute_product_qty(self):
        _logger.info("_compute_product_qty qty_producing: %s", self.qty_producing)
        res = super()._compute_product_qty()
        for rec in self:
            rec.formula_id = rec.bom_id.formula_id
            rec.formula_type = rec.bom_id.formula_type
            rec.validate_quantity = rec.bom_id.validate_quantity

        return res

    @api.onchange('formula_quantity')
    def _onchange_formula_quantity(self):
        for rec in self:
            rec._set_finish_goods_volume(rec.move_finished_ids.filtered(lambda x: x.product_id == rec.product_id))

    @api.model
    def _set_finish_goods_volume(self, move_ids):
        for move in move_ids:
            move.write({
                'volume': self.formula_quantity,
                'formula_id': self.formula_id.id,
                'formula_variables': self.formula_variables,
            })

            for move_line in move.move_line_ids:
                move_line.write({
                    'volume': self.formula_quantity,
                    'formula_id': self.formula_id.id,
                    'formula_variables': self.formula_variables,
                })

                quants = self.env['stock.quant']._gather(
                    move_line.product_id, move_line.location_dest_id, lot_id=move_line.lot_id
                )
                for quant in quants:
                    quant.write({
                        'volume': self.formula_quantity,
                        'formula_id': self.formula_id.id,
                        'formula_variables': self.formula_variables,
                    })

    def _get_move_finished_values(
            self, product_id, product_uom_qty, product_uom, operation_id=False,
            byproduct_id=False, cost_share=0
    ):
        data = super()._get_move_finished_values(
            product_id, product_uom_qty, product_uom,
            operation_id, byproduct_id, cost_share
        )
        if not byproduct_id:
            data['formula_id'] = self.formula_id.id
            data['formula_variables'] = self.formula_variables
            data['volume'] = self.formula_quantity

        return data

    def button_mark_done(self):
        res = super().button_mark_done()
        for rec in self:
            rec._set_finish_goods_volume(rec.move_finished_ids.filtered(lambda x: x.product_id == rec.product_id))

        return res

    def action_view_mrp_batch(self):
        self.ensure_one()
        if not self.mrp_batch_id:
            return

        return {
            'name': 'Manufacturing Orders',
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production.batch',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.mrp_batch_id.id,
        }

    def action_view_sale_order(self):
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


class MrpRandomFormulaCalculator(models.Model):
    _name = 'mrp.random.formula.calculator'
    _description = 'Random Formula Calculator'

    note = fields.Text(string="Note")
    production_id = fields.Many2one('mrp.production', string="Production Order")
    dimension = fields.Float(string="Dimension")
    quantity = fields.Float(string="Quantity")
    total = fields.Float(string="Total", compute='_compute_total')
    value_type = fields.Selection([
        ('width', 'Width'),
        ('length', 'Length'),
    ], string="Value Type")

    @api.depends('dimension', 'quantity')
    def _compute_total(self):
        for rec in self:
            rec.total = rec.dimension * rec.quantity


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    shift_type = fields.Selection([
        ('morning', 'Morning'),
        ('evening', 'Evening'),
        ('night', 'Night'),
    ], string='Shift')
    work_station_id = fields.Many2one("mrp.workcenter", string="Work Center")
    sequence = fields.Integer(string="Sequence", default=10, index=True)
    start_time = fields.Float(string="Start Time")
    end_time = fields.Float(string="End Time")
    default_shift = fields.Boolean(string="Default Shift")
    note = fields.Text(string="Remark")
