{
    'name': 'Odoo 17 Recurring Payment',
    'author': 'Odoo Mates',
    'category': 'Accounting',
    'version': '1.0.0',
    'description': """Odoo 17 Recurring Payment, Recurring Payment In Odoo, Odoo 17 Accounting""",
    'summary': 'Use recurring payments to handle periodically repeated payments',
    'sequence': 11,
    'depends': ['account'],
    'data': [
        'data/sequence.xml',
        'data/recurring_cron.xml',
        'security/ir.model.access.csv',
        'views/recurring_template_view.xml',
        'views/recurring_payment_view.xml'
    ],
    'images': ['static/description/banner.png'],
}
