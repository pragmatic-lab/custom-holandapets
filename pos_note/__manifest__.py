{
    'name': 'POS Note',
    'version': '1.0.0.0',
    'category': 'Point of Sale',
    'description': """
""",
    'author': 'Carlos Lopez Mite(celm1990@hotmail.com)',
    'depends': [
        'base',
        'mail',
        'web',
        'point_of_sale',
        'pos_base',
    ],
    'excludes': [
        'pos_order_note',
    ],
    'data': [
        'views/pos_config_view.xml',
        'views/pos_order_view.xml',
        'views/pos_note_assets.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml'
    ],
    'installable': True,
}
