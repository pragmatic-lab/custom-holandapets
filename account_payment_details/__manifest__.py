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
    'name': 'Account Payment Inherit',
    'category': 'Account',
    'version': '12.0',
    'author': 'Brayhan Andres Jaramillo Castaño' ,
    'license': 'LGPL-3',
    'maintainer': 'brayhanjaramillo@hotmail.com',
    'website': '',
    'summary': '',
    'images': [],

    'description': """

        Módulo que permite imprimir los apuntes contables en los pagos
    """,
    
    'depends': [ 'account', 'num_to_words'],


    'data': [
    
        'report/report_payment_receipt_document_inherit.xml',
        'views/account_payment_view_inherit.xml',

    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
