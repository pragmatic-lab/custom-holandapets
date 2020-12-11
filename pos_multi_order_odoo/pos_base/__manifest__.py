{
    'name': 'POS Base',
    'version': '1.0.0.0',
    'category': 'Point of Sale',
    'summary': """Modulo tecnico, sirve de base para otros modulos del POS""",
    'sequence': 5,
    'author': 'Carlos Eduardo Lopez Mite',
    'website': 'http://blaze-otp.com',
    'depends': [
        'point_of_sale',
    ],
    'data': [
        'views/pos_assets.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml'
    ],
    'installable': True,
    'auto_install': False,
}
