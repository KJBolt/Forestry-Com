from odoo import api, fields, models, _, Command


class CrossCutLogLine(models.Model):
    _inherit = 'cross.cut.log.line'

    hauling_id = fields.Many2one('hauling.hauling', string='Hauling')


class Hauling(models.Model):
    _name = 'hauling.hauling'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Hauling'
    _order = 'id desc'

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

    cross_cut_id = fields.Many2one('cross.cut', string="Cross Cut Log Number", help="Cross Cut Log Number")
    log_line_ids = fields.One2many('cross.cut.log.line', 'hauling_id', string='Hauling Log')

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

    @api.onchange('cross_cut_id')
    def _onchange_cross_cut_log_id(self):
        if self.cross_cut_id:
            self.forest_id = self.cross_cut_id.forest_id.id
            self.plot_id = self.cross_cut_id.plot_id.id
            self.machine_id = self.cross_cut_id.machine_id.id
            self.operator_id = self.cross_cut_id.operator_id.id
            self.date = self.cross_cut_id.date
            self.machine_runtime = self.cross_cut_id.machine_runtime
            self.remarks = self.cross_cut_id.remarks
            self.log_line_ids = [Command.link(x.id) for x in self.cross_cut_id.mapped('line_ids.log_line_ids')]
            self.cross_cut_id = False

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
        vals['name'] = self.env['ir.sequence'].next_by_code('hauling.hauling')
        result = super(Hauling, self).create(vals)
        return result
