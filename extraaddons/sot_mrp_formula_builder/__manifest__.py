{
    'name': 'Formula Builder',
    'version': '17.0.1.0.5',
    'category': 'Manufacturing/Tools',
    'summary': 'Calculate raw materia consumption quantity based on formula.',
    "description": """
      Input the formula values to get the quantity to consume for a raw material.
    """,
    'depends': ['stock'],
    'data': [
        'security/ir.model.access.csv',

        'wizards/formula_check_wizard_views.xml',
        'views/formula_views.xml',

        'data/math_function.xml',
    ],

    "images": [],

    "assets": {
        'web.assets_backend': [
            'sot_mrp_formula_builder/static/src/components/**/*',
        ],
    },
}
