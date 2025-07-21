{
    'name': 'Odoo 17 Fiscal Year & Lock Date',
    'version': '17.0.1.2',
    'category': 'Accounting',
    'summary': 'Odoo 17 Fiscal Year, Fiscal Year in Odoo 17, Lock Date in Odoo 17',
    'description': 'Odoo 17 Fiscal Year, Fiscal Year in Odoo 17',
    'sequence': '1',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'security/account_security.xml',
        'wizard/change_lock_date.xml',
        'views/fiscal_year.xml',
        'views/settings.xml',
    ],
    'images': ['static/description/banner.png'],
}
