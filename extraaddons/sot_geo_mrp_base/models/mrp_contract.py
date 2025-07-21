from odoo import api, fields, models


class Marking(models.Model):
    _name = 'mrp.markings'
    _description = 'Markings'

    name = fields.Char(string="Marking", required=True)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    amount = fields.Float(string="Amount")
    remarks = fields.Char(string="Remarks")



class Contract(models.Model):
    _name = 'mrp.contract'
    _description = 'Contracts'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'contract_no'


    contract_no = fields.Char(string="Contract No", required="True")
    buyer_name = fields.Many2one('res.partner',string="Buyer Name", required=True)
    representative = fields.Many2one('res.partner', string="Representative", required="True")
    phone_no = fields.Char(related="buyer_name.phone", string="Phone No", required="True")
    price = fields.Float(string="Price", required="True")
    email = fields.Char(related="buyer_name.email", string="Email", required="True")
    date = fields.Date(string="Date", required="True")
    specification_no = fields.Char(string="Specification No", required="True")
    delivery_start_date = fields.Date(string="Delivery Start Date", required="True")
    delivery_end_date = fields.Date(string="Delivery End Date", required="True")
    marking_ids = fields.Many2many('mrp.markings', string="Marking", required="False", help="Add one or more markings for this contract.")
    status = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ], string="Status", default='new')

    # Details Tab
    products = fields.Many2many('product.product', string="Products", required="True")

    # Destination Tab
    address_line1 = fields.Char(string="Address Line 1", required="False")
    address_line2 = fields.Char(string="Address Line 2", required="False") 
    country = fields.Char(string="Country", required="False")
    city = fields.Char(string="City", required="False")
    postal_code = fields.Char(string="Postal Zip Code", required="False")

    # Payment Tab
    date_of_payment = fields.Date(string="Date of Payment", required="False")
    mode_of_payment = fields.Selection([
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('bank_transfer', 'Bank Transfer'),
    ], string="Mode of Payment", required="False")
    amount = fields.Float(string="Amount", required="False")
    terms_of_payment = fields.Text(string="Terms of Payment", required="False")



    
