import logging

from odoo import api, fields, models, _, Command
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CrossCut(models.Model):
    _name = 'cross.cut'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Cross Cut'

    name = fields.Char(string="Serial No", required=True, default=lambda self: _("New"), tracking=True, readonly=True)
    forest_id = fields.Many2one('forest.reverse', string='Forest', required=True)
    forest_type_id = fields.Many2one('forest.type', string='Forest Type', related='forest_id.forest_type', store=True)
    supplier_id = fields.Many2one('res.partner', string='Supplier', related='forest_id.supplier_id', store=True)
    plot_id = fields.Many2one('forest.reverse.line', string='Plot/Compartment', required=True)
    machine_id = fields.Many2one('machine.machine', string='Machine', required=True)
    machine_runtime = fields.Float(string='Machine Runtime', required=True)
    operator_id = fields.Many2one('res.users', string='Operator', required=True)

    date = fields.Date(string='Date', required=True)
    remarks = fields.Text(string='Remarks')

    line_ids = fields.One2many('cross.cut.log', 'cross_cut_id', string='Cross Cut Line')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('cancel', 'Canceled')],
        default='draft',
        string="Status",
        tracking=True,
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

    @api.constrains('line_ids')
    def _check_line_ids(self):
        for rec in self:
            if not rec.line_ids:
                raise ValidationError(_("Please add cross cut details."))

            for line in rec.line_ids:
                if line.volume < 0:
                    raise ValidationError(_("Volume must be positive."))

                if line.logs_count < 0:
                    raise ValidationError(_("Logs count must be positive."))

                if not line.log_line_ids:
                    raise ValidationError(_("Please add log details"))

                # if line.max_length < sum(line.log_line_ids.mapped('length')):
                #     raise ValidationError(_("Cross cut lot length exceeds the maximum length."))

    def action_approve(self):
        for rec in self:
            for line in rec.line_ids:
                line.tree_id.is_used = True

            rec.write({'state': 'approved'})

    def action_cancel(self):
        for rec in self:
            rec.write({'state': 'cancel'})

    def action_reset_draft(self):
        for rec in self:
            rec.write({'state': 'draft'})

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('cross.cut')
        result = super(CrossCut, self).create(vals)
        return result


class CrossCutLog(models.Model):
    _name = 'cross.cut.log'
    _description = 'Cross Cut Line'
    _rec_name = 'tree_id'

    def _default_uom(self):

        uom = self.env.ref('uom.product_uom_cubic_meter', raise_if_not_found=False)
        return uom.id

    forest_id = fields.Many2one('forest.reverse', string='Forest')
    plot_id = fields.Many2one('forest.reverse.line', string='Plot/Compartment')
    cross_cut_id = fields.Many2one('cross.cut', string='Cross Cut', required=True, ondelete='cascade')
    tree_id = fields.Many2one('forest.tree.line', string='Stock Number', required=True)
    product_id = fields.Many2one(
        "product.product", related="tree_id.product_id",
        string="Species", help="Product with species attribute"
    )
    volume = fields.Float(string='Volume', compute='_compute_total_volume', store=True, digits='Volume')
    volume_uom_id = fields.Many2one('uom.uom', string='UoM', required=True, default=_default_uom)
    logs_count = fields.Integer(string='No of Logs', required=True)
    log_line_ids = fields.One2many('cross.cut.log.line', 'log_id', string='Cross Cut Logs')

    log_line_count = fields.Integer(string='#of Cross Cut Logs', compute='_compute_log_line_count', store=True)

    @api.depends('log_line_ids')
    def _compute_log_line_count(self):
        for record in self:
            record.log_line_count = len(record.log_line_ids)

    # The volume in cross cut now reflects the total volume in log line
    @api.depends('log_line_ids.quantity')
    def _compute_total_volume(self):
        for record in self:
            record.volume = sum(record.log_line_ids.mapped('quantity'))

    # @api.depends('log_line_ids', 'tree_id')
    # def _compute_remaining_length(self):
    #     for rec in self:
    #         domain = [('tree_id', '=', rec.tree_id.id)]
    #         if rec._origin:
    #             domain.append(('log_id', '!=', rec._origin.id))
    #
    #         previously_claimed_length = self.env['cross.cut.log.line'].search(domain).mapped('length')
    #         length_new = 0
    #
    #         for line in rec.cross_cut_id.mapped('line_ids.log_line_ids').filtered(
    #                 lambda x: x.tree_id.id == rec.tree_id.id):
    #             length_new += line.length
    #
    #         length = rec.max_length - (sum(previously_claimed_length) + length_new)
    #         rec.remaining_length = length > 0 and length or 0

    @api.onchange('logs_count', 'tree_id')
    def _onchange_logs_count(self):
        if self.logs_count and self.tree_id:
            name = [self.tree_id.name]
            self.log_line_ids = False

            tree_felling_line_id = self.env['forest.tree.felling.line'].search([('tree_id', '=', self.tree_id.id)])
            if tree_felling_line_id:
                tree_felling_line_id = tree_felling_line_id[0]
                if tree_felling_line_id.contr_tree_no:
                    name.append(tree_felling_line_id.contr_tree_no)

            name = "-".join(name)
            domain = [('tree_id', '=', self.tree_id.id)]
            if self._origin:
                domain.append(('log_id', '!=', self._origin.id))

            next_number = self.env['cross.cut.log.line'].search_count(domain) + 1

            if self != self._origin:
                for line in self.cross_cut_id.mapped('line_ids.log_line_ids'):
                    if line.tree_id.id == self.tree_id.id:
                        next_number += 1

            # length = self.remaining_length or 0.0
            # if length:
            #     length = length / (self.logs_count + next_number - 1)
            #     if length <= 0:
            #         length = 0

            self.log_line_ids = [Command.clear()] + [Command.create({
                'name': '%s-%s' % (name, next_number + index),
                'tree_id': self.tree_id.id,
                'volume_uom_id': tree_felling_line_id and tree_felling_line_id.unit_id.id,
                'defect_id': tree_felling_line_id and tree_felling_line_id.defect_id.id,
            }) for index in range(self.logs_count)]
            self.log_line_ids._onchange_product_set_formula()
        else:
            self.log_line_ids = False

    @api.onchange('tree_id', 'logs_count')
    def get_tree_volume(self):
        tree_felling_line_id = self.env['forest.tree.felling.line'].search(
            [('tree_id', '=', self.tree_id.id), ('forest_felling_id.state', '=', 'approved')])
        if tree_felling_line_id:
            total_length = 0
            # for rec in self.log_line_ids:
            #     total_length += rec.length

            self.volume = tree_felling_line_id.quantity
            # length_variable = self.env['formula.variable'].search([('name', '=', 'length')], limit=1)
            # self.max_length = tree_felling_line_id.formula_values.get(length_variable.id, 0)


class CrossCutLogDetails(models.Model):
    _name = 'cross.cut.log.line'
    _description = 'Cross Cut Log Details'

    def _default_uom(self):
        uom = self.env.ref('uom.product_uom_cubic_meter', raise_if_not_found=False)
        return uom.id

    log_id = fields.Many2one('cross.cut.log', string='Cross Cut Line', ondelete='cascade')
    forest_id = fields.Many2one('forest.reverse', string='Forest')
    plot_id = fields.Many2one('forest.reverse.line', string='Plot/Compartment')
    tree_id = fields.Many2one('forest.tree.line', string='Stock Number')
    product_id = fields.Many2one("product.product", related="tree_id.product_id", string="Product", )
    name = fields.Char(
        string="Cross Cut Log Number", help="Cross Cut Log Number", required=True, default=lambda self: _("New"),
        tracking=True, readonly=True
    )
    volume_uom_id = fields.Many2one('uom.uom', string='UoM', default=_default_uom)
    defect_id = fields.Many2one(
        "account.analytic.account",
        string="Defect",
    )
    remarks = fields.Text(string='Remarks')

    # Calculate Volume/Qty using formula
    formula_id = fields.Many2one('formula.formula', string="Product Type", tracking=True)
    formula_html = fields.Html(string="Formula Preview", related='formula_id.formula_html', readonly=True)
    formula_text = fields.Text(string="Formula Text", related='formula_id.formula', readonly=True)
    formula_variables = fields.Json(string='Formula Variables', related='formula_id.variables')
    formula_values = fields.Json(string='Formula Values')
    quantity = fields.Float(string="Volume", digits='Volume')

    @api.onchange('product_id', 'tree_id')
    def _onchange_product_set_formula(self):
        if self.product_id:
            self.formula_id = self.product_id.product_tmpl_id.formula_id.id
            self.formula_values = {}
