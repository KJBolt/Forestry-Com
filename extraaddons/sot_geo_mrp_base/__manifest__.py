{
    'name': 'Manufacturing Extend',
    'version': '17.0.1.0.5',
    'category': 'Manufacturing/Manufacturing',
    'summary': 'Manufacturing',
    "description": """
      Manufacturing
    """,
    'depends': ['sale_mrp', 'hr', 'sot_mrp_formula_builder', 'sot_stock_forestry'],
    'data': [
        'security/ir.model.access.csv',

        'views/res_config_settings_views.xml',
        'views/mrp_bom_views.xml',
        'views/mrp_production_views.xml',
        'views/mrp_workcenter_views.xml',
        'views/mrp_routing_workcenter_views.xml',
        'views/mrp_batch_views.xml',
        'views/sale_order_views.xml',
        'views/mrp_menus.xml',
        'views/mrp_contract.xml',

        'data/ir_sequence.xml',
    ],
    "images": ['static/description/icon.png'],
}
