{
    'name': 'Odoo 17 Budget Management',
    'category': 'Accounting',
    'version': '17.0.1.0',
    'description': """Use budgets to compare actual with expected revenues and costs""",
    'summary': 'Odoo 17 Budget Management',
    'sequence': 10,
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'security/account_budget_security.xml',
        'views/account_analytic_account_views.xml',
        'views/account_budget_views.xml',
        'views/res_config_settings_views.xml',
    ],
    "images": ['static/description/banner.gif'],
    'demo': ['data/account_budget_demo.xml'],
}
