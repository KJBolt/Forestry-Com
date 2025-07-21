from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    active = fields.Boolean(string="Active", default=True)
    is_species = fields.Boolean(string="Is Species")
    inactive_datetime = fields.Date(string="Inactive Date")
    inactive_reason = fields.Text(string="Inactive Reason")
    note = fields.Text(string="Description")

    @api.constrains('inactive_datetime')
    def _check_inactive_datetime(self):
        for rec in self:
            if rec.inactive_datetime and rec.inactive_datetime <= fields.date.today():
                raise ValidationError(_("Please selected Future Date."))

    def _cron_inactive_product_attribute(self):
        product_attribute_ids = self.env['product.attribute'].sudo().search(
            [('inactive_datetime', '=', fields.Date.today())]
        )
        product_attribute_ids.write({'active': False})


class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    species = fields.Char(string="Species")
    scientific_name = fields.Char(string="Scientific Name")
    note = fields.Char(string="Description")

    @api.depends('attribute_id', 'species')
    @api.depends_context('show_attribute')
    def _compute_display_name(self):
        for value in self:
            if value.species:
                value.display_name = f"[{value.species}] {value.name}"
            else:
                super(ProductAttributeValue, value)._compute_display_name()
