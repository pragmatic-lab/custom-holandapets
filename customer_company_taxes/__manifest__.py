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
    'name': 'Customer Company Taxes',
    'category': 'Taxes',
    'version': '12.0',
    'author': 'Brayhan Andres Jaramillo Castaño' ,
    'license': 'LGPL-3',
    'maintainer': 'brayhanjaramillo@hotmail.com',
    'website': '',
    'summary': '',
    'images': [],

    'description': """

        Módulo para incluir los impuestos a cargo del cliente o a cargo de la compañia

    """,
    
    'depends': [ 'account', 'website_sale', 'sale', 'account_invoice_pricelist', 'base',  'auth_signup', 'product'],

    'data': [
    
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/taxes_collected_view.xml',
        'views/sale_order_view_inherit.xml',
        'views/account_invoice_view_inherit.xml',
        'views/menu.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': False,
    'application': True,
    'auto_install': False,
}
