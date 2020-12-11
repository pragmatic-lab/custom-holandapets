# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    Autor: Brayhan Andres Jaramillo Castaño
#    Correo: brayhanjaramillo@hotmail.com
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################

{
    'name': 'POS Inherit',
    'version': '12.0.1.0.0',
    'summary': """Edit Pos""",
    'description': '',
    'author': "Brayhan Andres Jaramillo Castaño",
    'maintainer': 'brayhanjaramillo@hotmail.com',
    'category': 'Point of Sale',
    'depends': ['point_of_sale', 'product', 'product_warehouse_quantity', 'pos_stock_realtime', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'security/security.xml',
        'views/pos_cash.xml',
        #'views/pos_cash_details.xml',
        'views/pos_detail_cash.xml',
        'views/res_partner_inherit_view.xml',
        'views/pos_cash_inherit.xml',
        'views/pos_session_view_inherit.xml',
        'views/pos_cash_in_out.xml',
        'views/pos_order_view_inherit.xml',
        'views/edit_payment_method.xml'
       
    ],
    'qweb': ['static/src/xml/*.xml'],
    'demo': [],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
