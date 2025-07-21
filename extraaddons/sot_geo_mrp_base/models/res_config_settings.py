from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    allow_bom_cycle = fields.Boolean(
        string="Allow Production Cycle", config_parameter='sot_geo_mrp_base.allow_bom_cycle'
    )
