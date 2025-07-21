from odoo import _, api, fields, models
from odoo.exceptions import UserError


class FormulaCheckWizard(models.TransientModel):
    _name = 'formula.check.wizard'
    _description = 'Formula CHeck Wizard'
    _rec_name = "formula_id"


    formula_id = fields.Many2one('formula.formula', string='Formula')
    formula_text = fields.Text(related='formula_id.formula', string='Formula')
    variables = fields.Json(related='formula_id.variables', string='Dynamic Values')
    formula_values = fields.Json(string='Formula Values')

    formula_quantity = fields.Float(string="Formula Quantity", default=0)

    def action_check_formula(self):
        self.formula_id.action_activate_formula()



    
