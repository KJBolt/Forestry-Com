from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
import io
import xlsxwriter
import logging
import base64
import xlrd
from datetime import datetime

_logger = logging.getLogger(__name__)

# Custom Import Logic for tree registration
class ForestTreeImportWizard(models.TransientModel):
    _name = 'forest.tree.import.wizard'
    _description = 'Forest Tree Import Wizard'

    file = fields.Binary(string='Excel File')
    file_name = fields.Char('File Name')
    
    def action_import(self):
        """Import trees and their lines from Excel file, grouping by forest name"""
        self.ensure_one()
        
        if not self.file:
            raise UserError(_('Please select a file to import.'))
            
        try:
            # Read the Excel file
            file_data = base64.b64decode(self.file)
            workbook = xlrd.open_workbook(file_contents=file_data)
            sheet = workbook.sheet_by_index(0)
            
            # Get column indices (normalize header names by stripping and converting to lowercase)
            header = [str(cell.value).strip().lower() for cell in sheet.row(0)]
            required_forest_fields = ['forest name', 'plot/compartment', 'stripe line', 'latitude', 'longitude']
            required_tree_fields = ['stock number', 'species', 'diameter', 'Length UoM(m)', 'condition score']
            
            # Check for required fields (case-insensitive)
            missing_forest_fields = [f for f in required_forest_fields if f.lower() not in [h.lower() for h in header]]
            missing_tree_fields = [f for f in required_tree_fields if f.lower() not in [h.lower() for h in header]]
            
            if missing_forest_fields or missing_tree_fields:
                error_msg = []
                if missing_forest_fields:
                    error_msg.append(f"Forest registration fields: {', '.join(missing_forest_fields)}")
                if missing_tree_fields:
                    error_msg.append(f"Tree line fields: {', '.join(missing_tree_fields)}")
                raise UserError(_('Required column(s) not found in the Excel file: \n%s') % '\n'.join(error_msg))
            
            # Create a mapping of normalized header names to column indices
            header_map = {h.lower().strip(): idx for idx, h in enumerate(header)}
            
            # Group rows by forest name
            forest_groups = {}
            
            # Process each row (skip header)
            for row_idx in range(1, sheet.nrows):
                row_data = sheet.row(row_idx)
                row = {}
                for h, idx in header_map.items():
                    row[h] = row_data[idx].value if idx < len(row_data) and row_data[idx].value is not None else ''
                
                # Skip empty rows
                if not any(str(v).strip() for v in row.values() if v is not None):
                    continue
                    
                forest_name = str(row.get('forest name', '')).strip()
                if not forest_name:
                    continue
                    
                if forest_name not in forest_groups:
                    forest_groups[forest_name] = []
                forest_groups[forest_name].append(row)
            
            if not forest_groups:
                raise UserError(_('No valid forest data found in the file.'))
            
            tree_count = 0
            line_count = 0
            
            # Process each forest group
            for forest_name, rows in forest_groups.items():
                if not rows:
                    continue
                    
                # Get the first row for forest registration data
                first_row = rows[0]
                
                # Create forest registration record
                forest_id = self._get_forest_id(forest_name)
                plot_compartment_id = self._get_plot_compartment_id(first_row.get('plot/compartment', ''), forest_id)
                stripe_id = self._get_stripe_id(first_row.get('stripe line', ''), plot_compartment_id)
                
                tree_vals = {
                    'forest_reverse_id': forest_id,
                    'plot_compartment_id': plot_compartment_id,
                    'stripe_id': stripe_id,
                    'latitude': first_row.get('latitude', ''),
                    'longitude': first_row.get('longitude', ''),
                    'remarks': first_row.get('remarks', ''),
                }
                
                # Create the forest registration
                current_tree = self.env['forest.tree'].create(tree_vals)
                tree_count += 1
                
                # Add all tree lines for this forest
                for row in rows:
                    try:
                        line_vals = {
                            'tree_id': current_tree.id,
                            'name': row.get('stock number', ''),
                            'product_id': self._get_product_id(row.get('species', '')),
                            'diameter': int(row.get('diameter', 0)) if str(row.get('diameter', '')).strip() else 0,
                            'uom_id': self._get_uom_id(row.get('Length UoM(m)', '')),
                            'condition_score': float(row.get('condition score', 0)) if str(row.get('condition score', '')).strip() else 0.0,
                            'latitude': first_row.get('latitude', ''),
                            'longitude': first_row.get('longitude', ''),
                        }
                        self.env['forest.tree.line'].create(line_vals)
                        line_count += 1
                    except Exception as e:
                        _logger.error(f"Error creating tree line: {str(e)}")
                        continue
            
            # Show success notification and reload the page
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Successfully imported %s forests with %s tree lines.') % (tree_count, line_count),
                    'sticky': False,
                    'next': {
                        'type': 'ir.actions.client',
                        'tag': 'reload',
                    }
                }
            }
            
        except Exception as e:
            _logger.error(f"Error in tree import: {str(e)}", exc_info=True)
            raise UserError(_('Error importing file: %s') % str(e))
    
    def _get_forest_id(self, name):
        """Get or create forest by name"""
        if not name:
            raise UserError(_('Forest name is required.'))
            
        forest = self.env['forest.reverse'].search([('name', '=', name)], limit=1)
        if not forest:
            # Create the forest if it doesn't exist
            forest = self.env['forest.reverse'].create({
                'name': name,
                # Add any other required fields with default values
                'state': 'draft',  # Assuming there's a state field
            })
        return forest.id
    
    def _get_plot_compartment_id(self, name, forest_id):
        """Get or create plot/compartment by name under the given forest"""
        if not name:
            raise UserError(_('Plot/Compartment is required.'))
            
        plot = self.env['forest.reverse.line'].search([
            ('name', '=', name),
            ('reverse_id', '=', forest_id)
        ], limit=1)
        
        if not plot and forest_id:
            # Create the plot/compartment if it doesn't exist under this forest
            plot = self.env['forest.reverse.line'].create({
                'name': name,
                'reverse_id': forest_id,
                # Add any other required fields with default values
            })
        elif not plot:
            raise UserError(_('Forest not found for plot/compartment: %s') % name)
            
        return plot.id
    
    def _get_stripe_id(self, stripe_name, plot_compartment_id):
        """Get or create stripe by name under the given plot/compartment"""
        if not stripe_name or not plot_compartment_id:
            return False
            
        stripe = self.env['forest.reverse.line.stripe'].search([
            ('name', '=', stripe_name),
            ('reserve_line_id', '=', plot_compartment_id)
        ], limit=1)
        
        if not stripe and plot_compartment_id:
            # Create the stripe if it doesn't exist under this plot/compartment
            stripe = self.env['forest.reverse.line.stripe'].create({
                'name': stripe_name,
                'reserve_line_id': plot_compartment_id,
                # Add any other required fields with default values
            })
        
        return stripe.id if stripe else False
    
    def _get_product_id(self, species_name):
        """Get product ID by species name, create under Raw Material-RM category if not exists"""
        if not species_name:
            return False
            
        # First try to find existing product with exact name match in Raw Material-RM category
        product = self.env['product.product'].search([
            ('name', '=', species_name),
            ('categ_id.name', '=', 'Raw Material-RM')
        ], limit=1)
        
        if not product:
            # Get or create Raw Material-RM category
            category = self.env['product.category'].search([
                ('name', '=', 'Raw Material-RM')
            ], limit=1)
            
            if not category:
                # Create the category if it doesn't exist
                category = self.env['product.category'].create({
                    'name': 'Raw Material-RM',
                    'property_valuation': 'real_time',
                    'property_cost_method': 'fifo',
                })
            
            # Create the product under Raw Material-RM category
            product = self.env['product.product'].create({
                'name': species_name,
                'type': 'product',
                'categ_id': category.id,
                'default_code': species_name[:10].upper().replace(' ', ''),
                'purchase_ok': True,
                'sale_ok': False,  # Typically raw materials are not sold directly
                'tracking': 'lot',  # Track by lots for better inventory management
            })
            
            _logger.info(f"Created new product: {species_name} under Raw Material-RM category")
            
        return product.id
    
    def _get_uom_id(self, uom_name):
        """Get UoM ID by name, default to meters if not found"""
        if not uom_name:
            return self.env.ref('uom.product_uom_meter').id
            
        uom = self.env['uom.uom'].search([('name', 'ilike', uom_name)], limit=1)
        return uom.id if uom else self.env.ref('uom.product_uom_meter').id



    # Download Excel Template
    def download_template(self):
        # Create an in-memory file
        output = io.BytesIO()

        # Create an Excel workbook and worksheet
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # Create bold format
        bold_format = workbook.add_format({'bold': True})

        # Define headers
        headers = ['Forest Name', 'Plot/Compartment', 'Stripe Line', 'Latitude', 'Longitude', 'Remarks', 'Stock Number', 'Species', 'Diameter', 'Length UoM(m)', 'Condition Score', ]

        # Write headers with bold format
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, bold_format)

        # Close workbook
        workbook.close()
        output.seek(0)

        # Create attachment and return file data
        attachment = self.env['ir.attachment'].create({
            'name': 'tree_registration_template.xlsx',
            'datas': base64.b64encode(output.getvalue()),
            'type': 'binary',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self'
        }
        


class ForestTreeRegister(models.Model):
    _name = "forest.tree"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Forest Tree Register"
    _order = 'id desc'

    active = fields.Boolean(string="Active", default=True)
    note = fields.Text(string="Note")
    name = fields.Char(string="Serial No", required=True, default=lambda self: _("New"), tracking=True, readonly=True)
    forest_reverse_id = fields.Many2one("forest.reverse", string="Forest Name")
    diameter = fields.Integer(string="Diameter")
    remarks = fields.Text(string="Remarks")
    plot_compartment_id = fields.Many2one('forest.reverse.line', string="Plot/Compartment")
    document_date = fields.Date(string="Document Date")
    stripe_id = fields.Many2one('forest.reverse.line.stripe', string="Strip Line")
    diameter_id = fields.Many2one("uom.uom", string="Diameter Type")
    latitude = fields.Char(related='plot_compartment_id.latitude', string="Latitude")
    longitude = fields.Char(related='plot_compartment_id.longitude', string="Longitude")

    line_ids = fields.One2many('forest.tree.line', 'tree_id', string="Forest Reverse Details")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('cancel', 'Canceled')],
        default='draft',
        string="Status",
        tracking=True,
    )

    @api.onchange('forest_reverse_id')
    def _onchange_forest_reverse_id(self):
        if self.forest_reverse_id:
            plot_compartment_id = self.env['forest.reverse.line'].search(
                [('reverse_id', '=', self.forest_reverse_id.id)], limit=1)
            if plot_compartment_id:
                if not plot_compartment_id.is_used_plot_compartment:
                    self.plot_compartment_id = plot_compartment_id.id
                else:
                    self.plot_compartment_id = False
            else:
                self.plot_compartment_id = False
        else:
            self.plot_compartment_id = False

    @api.onchange('plot_compartment_id')
    def _onchange_plot_compartment_id(self):
        if self.stripe_id.reserve_line_id != self.plot_compartment_id:
            self.stripe_id = False

    @api.constrains('line_ids')
    def _check_line_ids(self):
        for rec in self:
            if not rec.line_ids:
                raise ValidationError(_("Please add tree details."))

    def set_approved(self):
        for rec in self:
            rec.state = 'approved'
            rec.plot_compartment_id.is_used_plot_compartment = True

    def set_cancel(self):
        for rec in self:
            rec.state = 'cancel'
            rec.plot_compartment_id.is_used_plot_compartment = False

    def action_reset_draft(self):
        for rec in self:
            rec.write({'state': 'draft'})
            rec.plot_compartment_id.is_used_plot_compartment = False

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('forest.tree.registration')
        result = super(ForestTreeRegister, self).create(vals)
        return result


class ForestFellingLine(models.Model):
    _name = "forest.tree.line"
    _description = "Forest Tree Line"

    def _default_uom(self):
        uom = self.env.ref('uom.product_uom_meter', raise_if_not_found=False)
        return uom.id

    name = fields.Integer(string="Stock Number")

    # Get Raw material species
    product_id = fields.Many2one(
        "product.product", 
        string="Species", 
        help="Product with species attribute",
        domain="[('categ_id.name', 'ilike', 'Raw Material-RM')]"
    )
    species_id = fields.Many2one("product.attribute.value", string="Species")
    tree_id = fields.Many2one('forest.tree', string="Parent")
    forest_reverse_id = fields.Many2one('forest.reverse', related='tree_id.forest_reverse_id', string="Forest Name")
    plot_compartment_id = fields.Many2one(
        'forest.reverse.line', related='tree_id.plot_compartment_id',
        string="Plot/Compartment"
    )
    condition_score = fields.Float(string="Condition Score")
    diameter = fields.Integer(string="Diameter")
    uom_id = fields.Many2one("uom.uom", string="UoM", default=_default_uom)
    latitude = fields.Char(string="Latitude")
    longitude = fields.Char(string="Longitude")
    approved = fields.Boolean(string="Approved?")
    is_used = fields.Boolean(string="Is Used?")
    state = fields.Selection([
        ('standing', 'Standing'),
        ('fallen', 'Fallen')],
        default='standing',
        string="Status"
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            # Get all attribute values linked to the selected product
            product_template = self.product_id.product_tmpl_id

            # Get the 'species' attribute based on your is_species field
            species_attribute = self.env['product.attribute'].search([('is_species', '=', True)], limit=1)

            if species_attribute:
                # Filter product's attribute values related to the 'Species' attribute
                species_values = product_template.valid_product_template_attribute_line_ids.mapped(
                    'value_ids').filtered(
                    lambda val: val.attribute_id == species_attribute
                )

                # Return a domain to restrict the species_id dropdown to these filtered values
                return {'domain': {'species_id': [('id', 'in', species_values.ids)]}}
        else:
            # No product selected, so clear the domain
            return {'domain': {'species_id': []}}

    @api.constrains('state')
    def _check_state(self):
        for rec in self:
            if rec.state == 'fallen' and not rec.approved:
                raise ValidationError(_("Please approve the tree before falling it."))

            if rec._origin and rec._origin.state == 'fallen' and rec.state != 'fallen':
                raise ValidationError(_("You cannot change the state of a fallen tree."))

    def action_approve(self):
        for rec in self:
            rec.approved = True

    def action_unapprove(self):
        fallen_tree_exists = self.filtered(lambda x: x.state == 'fallen')
        if fallen_tree_exists:
            raise ValidationError(_("You cannot unapprove a fallen tree."))

        for rec in self:
            rec.approved = False

    def preview_lat_log(self):
        self.ensure_one()
        if not self.latitude or not self.longitude:
            raise UserError("Latitude and Longitude must be set to preview the map.")

        return {
            'type': 'ir.actions.act_url',
            'target': '_blank',
            'url': f"https://www.google.com.sa/maps/search/{self.latitude},{self.longitude}",
        }
