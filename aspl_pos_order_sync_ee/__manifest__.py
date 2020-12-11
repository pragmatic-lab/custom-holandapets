# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################
{
    'name': 'POS Order Synchronization (Enterprise)',
    'version': '1.0',
    'author': 'Acespritech Solutions Pvt. Ltd.',
    'summary': 'POS Order sync between Salesman and Cashier',
    'description': "Allow salesperson to only create draft order and send draft order to Cashier for payment",
    'category': 'Point Of Sale',
    'website': 'http://www.acespritech.com',
    'depends': [
        'base',
        'point_of_sale',
        'pos_base',
        'pos_cashier_select',
        'pos_orders_history',
        'pos_note',
        'pos_rounding',
    ],
    'price': 25.00, 
    'currency': 'EUR',
    'images': [
         'static/description/main_screenshot.png',
     ],
    'data': [
        'views/aspl_pos_order_sync_reg.xml',
        'views/pos_view.xml',
        'views/res_users_view.xml'
    ],
     'qweb': [
        'static/src/xml/pos.xml'
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
