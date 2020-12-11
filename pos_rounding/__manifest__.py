{
    'name': 'POS Rounding',
    'version': '12.0.0.0.0',
    'category': 'Point of Sale',
    'summary': """Permite redondear el total del pedido(en base a cantidad de digitos o precision decimal)""",
    'sequence': 5,
    'author': 'Flectra Chile SPA',
    'website': 'http://flectrachile.cl/',
    'depends': [
        'base', 
        'point_of_sale',
        'pos_base',
    ],
    'data': [
        'views/pos_config_view.xml',
        'views/pos_order_view.xml',
        'views/pos_rounding_assets.xml'
    ],
    'qweb': [
        'static/src/xml/pos.xml'
    ],
    'installable': True,
    'application': True,
}
