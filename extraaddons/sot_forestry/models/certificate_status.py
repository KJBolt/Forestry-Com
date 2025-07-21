from odoo import fields, models

class ForestReverseCertificateStatus(models.Model):
    _name = "certificate.status"
    _inherit = ['mail.thread', 'mail.activity.mixin'] 
    _description = "Certificate Status"

    name = fields.Char(string="Name", required=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string="Active", default=True)
    note = fields.Text(string="Note")
