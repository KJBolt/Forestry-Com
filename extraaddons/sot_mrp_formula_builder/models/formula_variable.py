from odoo import _, api, fields, models


class FormulaVariables(models.Model):
    _name = 'formula.variable'
    _description = 'Formula Variables'

    active = fields.Boolean(string='Active', default=True)
    name = fields.Char(string='Name', required=True)
    variable = fields.Char(string='Variable', required=True)

    _sql_constraints = [
        ('variable_unique', 'unique(variable)', _('Variable must be unique!')),
        ('variable_alphabet_only', 'CHECK(variable ~* \'^[a-zA-Z_][a-zA-Z0-9_]*$\')', _('Variable must be alphabet only!')),
    ]

    def get_all_formula_variable_dict(self):
        return {variable.id: variable.name for variable in self.search([])}