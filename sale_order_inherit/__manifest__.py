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
    'name': 'Sale Order Inherit',
    'category': 'Sales',
    'version': '12.0',
    'author': 'Brayhan Andres Jaramillo Castaño' ,
    'license': 'LGPL-3',
    'maintainer': 'brayhanjaramillo@hotmail.com',
    'website': '',
    'summary': '',
    'images': [],

    'description': """

        Módulo que permite la recepcion de toma de pedidos rapidamente para ser facturados

    """,
    
    'depends': ['base', 'stock', 'account', 'sale', 'discount_total',],


    'data': [
        
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/sale_order_conf_text_view.xml',
        'views/sale_order_view_inherit.xml',
        'views/product_pricelist_view_inherit.xml',
        'views/res_partner_view_inherit.xml',
        'views/account_invoice_view_inherit.xml',
        'views/menu.xml',
        'report/sale_order_ticket.xml',
        'report/account_invoice_ticket.xml',
        'views/product_template_view_inherit.xml',
        'views/account_invoice_payment_action_view.xml',
        'views/account_invoice_payment_action_confirm_view.xml',
        'views/product_template_inherit.xml',
        'views/res_user_view_inherit.xml',
        'views/account_payment_view_inherit.xml',
        'views/purchase_order_view_inherit.xml',
        'views/sale_order_conf_box_view.xml',
        'views/product_brand_inherit_view.xml',
        'report/purchase_order_document_inherit.xml'
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
