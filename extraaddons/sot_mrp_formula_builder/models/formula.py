import logging
import builtins

from odoo import fields, models, api
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval
from odoo.tools import float_compare, float_round

_logger = logging.getLogger(__name__)


class Formula(models.Model):
    _name = 'formula.formula'
    _description = 'Formula'

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    formula_editor = fields.Char(string='Formula Editor')
    formula_html = fields.Html(string='Formula Preview', compute='_compute_formula_html', help='Use css class o_field_formula_editor on field')
    formula = fields.Text(string='Output Formula')
    variable_id = fields.Many2one('formula.variable', string='Variable')
    function_id = fields.Many2one('formula.function', string='Function')
    variables = fields.Json(string='Dynamic Values', default={"variables": [], "functions": []})

    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
    ], string='State', default='draft')

    @api.depends('formula_editor')
    def _compute_formula_html(self):
        for rec in self:
            rec.formula_html = rec.formula_editor.replace('contenteditable', 'readonly') if rec.formula_editor else ""

    @api.onchange('variable_id')
    def _onchange_variable_id(self):
        if self.variable_id:
            self.formula_editor = f'{self.formula_editor} <span class="variable-span variables" contenteditable="false" data-id="{self.variable_id.id}" data-type="variables" data-value="{self.variable_id.variable}">{self.variable_id.variable}</span>'
            self.formula = f'{self.formula} {self.variable_id.variable}'
            self.variables['variables'].append(self.variable_id.id)

    @api.onchange('function_id')
    def _onchange_function_id(self):
        # if self.function_id:
        #     self.formula_editor = f'{self.formula_editor} <span class="variable-span functions" contenteditable="{self.function_id.content_editable}" data-id="{self.function_id.id}" data-type="functions" data-value="{self.function_id.function_name}">{self.function_id.function_name}{self.function_id.content_editable and '(1)' or ''}</span><span>{self.function_id.content_editable and ' ' or ''}</span>'
        #     self.formula = f'{self.formula} {self.function_id.function_name}'
        #     self.variables['functions'].append(self.function_id.id)
        if self.function_id:
            content_editable = str(self.function_id.content_editable).lower()  # convert boolean to 'true'/'false'
            function_name = self.function_id.function_name
            function_id = self.function_id.id
            editable_suffix = '(1)' if self.function_id.content_editable else ''
            space_suffix = ' ' if self.function_id.content_editable else ''
            
            span_html = (
                f'{self.formula_editor or ""} '
                f'<span class="variable-span functions" '
                f'contenteditable="{content_editable}" '
                f'data-id="{function_id}" '
                f'data-type="functions" '
                f'data-value="{function_name}">'
                f'{function_name}{editable_suffix}</span>'
                f'<span>{space_suffix}</span>'
            )
            
            self.formula_editor = span_html
            self.formula = f'{self.formula or ""} {function_name}'
            self.variables['functions'].append(function_id)

    def compute_formula(self, formula, formula_vals, default=0):
        try:
            if not formula:
                raise UserError("Formula is not defined.")

            _logger.info("Formula: %s" % formula)
            _logger.info("Formula Vals: %s" % formula_vals)

            functions = self.env['formula.function'].search([])
            variable_vals = {}
            for key, val in formula_vals.items():
                variable_id = self.env['formula.variable'].browse(int(key))
                variable_vals[variable_id.variable] = val

            for function in functions:
                variable_vals[function.function_name] = self.env['formula.function']._get_math_operation(
                    function.function_name
                )

            eval_globals = {**vars(builtins), **variable_vals}
            res = safe_eval(formula, eval_globals)
            _logger.info(res)
            dp = self.env['decimal.precision'].precision_get('Volume')
            return float_round(res, precision_digits=dp)
        except Exception as e:
            raise UserError(str(e))

    def action_activate_formula(self):
        self.state = 'active'

    def action_deactivate_formula(self):
        self.state = 'draft'
