import math
from odoo import _, api, fields, models

MATH_OPERATIONS={
    'add': '+',
    'subtract': '-',
    'multiply': '*',
    'divide': '/',
    'modulo': '%',
    'power': '**',
    'floor_divide': '//',
    'pi': math.pi,
    'sqrt': math.sqrt,
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'exp': math.exp,
    'factorial': math.factorial,
    'abs': math.fabs,
}

class FormulaFunction(models.Model):
    _name = 'formula.function'
    _description = 'Formula Function'

    active = fields.Boolean(string='Active', default=True)
    name = fields.Char(string='Name', required=True)
    function_name = fields.Char(string='Variable', required=True)
    sample_formula = fields.Text(string='Sample Formula')
    content_editable = fields.Boolean(string='Editable', default=False)

    @api.model
    def _get_math_operation(self, function_name):
        return MATH_OPERATIONS.get(function_name, function_name)
