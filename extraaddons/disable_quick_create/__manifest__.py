{
    'name': 'Disable M2o Quick Create/Edit',
    'version': '17.0.1.0.0',
    'sequence': 1,
    'depends': ['web'],
    'data': [],
    "images": ['static/description/icon.png'],
    'assets': {
        'web.assets_qweb': [],
        'web.assets_backend': [
            'disable_quick_create/static/src/**/*.js'
        ]
    },
    'summary': "Disable Many2one field quick create when option is undefined.",
    'description': """
*   Disable Many2one field quick create by default.
*   To Allow implicitly for a field for quick create set options as False in field.
    options="{'no_quick_create': False, 'no_create_edit': False, 'no_open': False, ...}"
""",
    'installable': True,
    'application': True,
    'auto_install': False,
}
