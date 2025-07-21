from odoo import fields, models

class ForestDistrict(models.Model):
    _name = "forest.district"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "District Info"

    name = fields.Char(string="Name", required=True, tracking=True)
    set_type = fields.Selection([
        ('property_mark', 'Property Mark'),
        ('species', 'Species'),
        ('defect', 'Defect'),
        ('district', 'District'),
        ('costing', 'COSTING'),
        ('feedback', 'FEEDBACK'),
        ('overhead', 'OVERHEAD'),
        ('down_time', 'DOWN TIME'),
        ],
        string="Set Type",
        tracking=True,
    )
    active = fields.Boolean(string="Active", default=True)
    note = fields.Text(string="Description")
