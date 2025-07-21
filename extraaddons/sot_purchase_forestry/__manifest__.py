{
    "name": "Forestry Purchase Management",
    "version": "17.0.0.2",
    "category": "Inventory/Purchase",
    'license': 'OPL-1',
    'summary': 'Purchase Management System for Large Scale Plantation Projects',
    "description": """
        This odoo app helps user to manage forestry projects, plantations, nurseries, and other forestry related activities. 
        User can manage forestry projects, plantations, nurseries, and other forestry related activities.
    """,
    "depends": ['sot_stock_forestry'],
    "data": [
        'reports/purchase_rqf_report.xml',
        'reports/purchase_rqf_template.xml',
        'reports/purchase_order_report.xml',
        'reports/purchase_order_template.xml',
        'views/purchase_views.xml',
    ],
    "qweb": [],
    "auto_install": False,
    "installable": True,
    "application": True,
}
