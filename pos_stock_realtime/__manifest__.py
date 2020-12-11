# -*- coding: utf-8 -*-
{
    'name': 'POS Stock Realtime',
    'version': '12.1.2',
    'category': 'Point Of Sale',
    'author': 'D.Jane, Fauniq',
    'price': 0,
    'currency': 'EUR',
    'license': 'OPL-1',
    'support': 'fauniq.erp@gmail.com',
    'sequence': 1,
    'summary': 'Display Stocks on POS Location. Update Real-Time available quantity if POS online.',
    'description': "",
    'depends': ['point_of_sale'],
    'data': [
        'views/assets.xml',
        'views/pos_config_view.xml'
    ],
    'images': ['static/description/banner.png'],
    'qweb': ['static/src/xml/pos_stock.xml'],
    'installable': True,
    'application': True,
}
