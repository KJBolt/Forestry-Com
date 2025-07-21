{
    'name': 'GEO Manufacturing Dashboard',
    'version': '17.0.1.0.5',
    'category': 'mrp',
    'summary': 'Manufacturing Dashboard',
    "description": """
        Manufacturing Dashboard
    """,
    'depends': ['sot_geo_mrp_base'],
    'data': [
        'security/ir.model.access.csv',
        'views/dashboard.xml',
        'views/mrp_menus.xml',
    ],

    'icon': "/geo_mrp_dashboard/static/description/icon.png",
    "images": ['static/description/icon.png'],

    'assets': {
        'web.assets_backend': [
            'geo_mrp_dashboard/static/src/components/**/*.js',
            'geo_mrp_dashboard/static/src/components/**/*.xml',
            'geo_mrp_dashboard/static/src/components/**/*.scss',
            'geo_mrp_dashboard/static/src/components/backend.css',
        ],
        'web.assets_common': [
            # Assets common to both frontend and backend
            'geo_mrp_dashboard/static/src/components/moment.min.js',
        ],
    },

}
