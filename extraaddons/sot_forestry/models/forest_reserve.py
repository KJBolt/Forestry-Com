import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ForestReverse(models.Model):
    _name = "forest.reverse"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Forest Reverse"
    _order = 'id desc'

    def _default_uom(self):
        uom = self.env.ref('uom.uom_square_meter', raise_if_not_found=False)
        return uom.id

    active = fields.Boolean(string="Active", default=True)
    note = fields.Text(string="Note")
    code = fields.Char(string="Serial No", default=lambda self: _("New"), tracking=True, readonly=True)
    forest_type = fields.Many2one('forest.type', string="Forest Type")
    name = fields.Char(string="Forest Name", required=True)
    district_id = fields.Many2one(
        "forest.district",
        string="District",
    )
    supplier_id = fields.Many2one('res.partner', string='Supplier Name', domain=[('customer_type','=','supplier')])
    certificate_no = fields.Char(string="Certificate No")
    fmu = fields.Char(string="FMU", size=10)
    area = fields.Float(string="Area")
    uom_id = fields.Many2one("uom.uom", string="UoM", default=_default_uom)
    forestry_code = fields.Char(string="Forestry Code")
    freeze = fields.Boolean(string="Freeze")

    property_mark_id = fields.Many2one(
        "forest.property.mark",
        string="Property Mark",
    )

    certification_status_id = fields.Many2one('certificate.status', string='Certificate Status')
    rate = fields.Float(string="Rate", digits='Product Price', )

    line_ids = fields.One2many(
        'forest.reverse.line', 'reverse_id', string="Forest Reverse Details",
        domain=['|', ('active', '=', False), ('active', '=', True)], context={'active_test': False}
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('cancel', 'Canceled'),
        ('close', 'Closed')],
        default='draft',
        string="Status",
        tracking=True,
    )

    any_active_lines = fields.Boolean(compute='_compute_any_active_lines', store=True)

    @api.depends('line_ids.active')
    def _compute_any_active_lines(self):
        for record in self:
            record.any_active_lines = any(line.active for line in record.line_ids)

    @api.model
    def create(self, vals):
        vals['code'] = self.env['ir.sequence'].next_by_code('forest.reverse')
        result = super(ForestReverse, self).create(vals)
        return result

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

    @api.constrains('line_ids')
    def _check_line_ids(self):
        for rec in self:
            if not rec.line_ids:
                raise ValidationError(_('Please add Plot/Compartment Details.'))

            for line in rec.line_ids:
                if not line.point_line_ids:
                    raise ValidationError(_('Please add Add Point Details.'))

                if not line.stripe_line_ids:
                    raise ValidationError(_('Please add Stripe Details.'))


class ForestReverseDetails(models.Model):
    _name = "forest.reverse.line"
    _description = "Plot/Compartment Details"

    def _default_uom(self):
        uom = self.env.ref('uom.uom_square_meter', raise_if_not_found=False)
        return uom.id

    active = fields.Boolean(string="Active", default=True)
    name = fields.Char(string="Plot/Compartment Name")
    note = fields.Text(string="Note")
    area = fields.Float(string="Area")
    area_uom_id = fields.Many2one("uom.uom", string="UoM", default=_default_uom)
    forestry_code = fields.Char(string="Forestry Code")
    circumference = fields.Boolean(string="Circumference")
    plantation = fields.Boolean(string="Plantation")
    is_used_plot_compartment = fields.Boolean(string="Is Used Compartment")
    price_applicable = fields.Boolean(string="Price Applicable", default=True)
    reverse_id = fields.Many2one('forest.reverse', string="Forest Reverse")
    latitude = fields.Char(string="Latitude")
    longitude = fields.Char(string="Longitude")
    embed_map = fields.Char(string="Map")

    point_line_ids = fields.One2many('forest.reverse.line.point', 'reserve_line_id', string="Forest Reverse AddPoint")
    coordinate_line_ids = fields.One2many('forest.reverse.line.coordinate', 'reserve_line_id', string="Forest Reverse AddCoordinate")
    stripe_line_ids = fields.One2many('forest.reverse.line.stripe', 'reserve_line_id', string="Forest Reverse Stripes Details")

    _sql_constraints = [
        ('name_reverse_id_uniq', 'unique(name,reverse_id)', 'Plot/Compartment Name must be unique per forest!'),
    ]

    @api.constrains('point_line_ids')
    def _check_point_line_ids(self):
        for rec in self:
            if not rec.point_line_ids:
                raise ValidationError(_('Please add Point Details.'))

    @api.constrains('stripe_line_ids')
    def _check_stripe_line_ids(self):
        for rec in self:
            if not rec.stripe_line_ids:
                raise ValidationError(_('Please add Stripe Details.'))


class ForestReversePoint(models.Model):
    _name = "forest.reverse.line.point"
    _description = "Forest Reverse Add Point"

    def _default_uom(self):
        uom = self.env.ref('uom.product_uom_meter', raise_if_not_found=False)
        return uom.id

    form_point = fields.Char(string="Form Point")
    to_point = fields.Char(string="To Point")
    distance = fields.Char(string="Distance")
    unit_id = fields.Many2one("uom.uom", string="UoM", default=_default_uom)
    reserve_line_id = fields.Many2one('forest.reverse.line', string="Plot/Compartment")
    active = fields.Boolean(string="Active", default=True)
    note = fields.Text(string="Note")


class ForestReverseCoordinates(models.Model):
    _name = "forest.reverse.line.coordinate"
    _description = "Forest Reverse Add Coordinate"

    latitude = fields.Char(string="Latitude")
    longitude = fields.Char(string="Longitude")
    reserve_line_id = fields.Many2one('forest.reverse.line', string="Plot/Compartment")
    active = fields.Boolean(string="Active", default=True)
    note = fields.Text(string="Note")


class ForestReversStripes(models.Model):
    _name = "forest.reverse.line.stripe"
    _description = "Forest Reverse Stripe"

    def _default_uom(self):
        uom = self.env.ref('uom.product_uom_meter', raise_if_not_found=False)
        return uom.id

    name = fields.Char(string="Strip Line")
    distance = fields.Integer(string="Distance")
    unit_id = fields.Many2one("uom.uom", string="UoM", default=_default_uom)
    reserve_line_id = fields.Many2one('forest.reverse.line', string="Plot/Compartment")
    active = fields.Boolean(string="Active", default=True)
    note = fields.Text(string="Note")
