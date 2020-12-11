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
    'name': 'Invoice Line Partner',
    'version': '12.0',
    'category': 'Accounting',
    'author': 'Brayhan Andres Jaramillo Castaño',
    'summary': 'Modelo que permite asignar los terceros al realizar el asiento contable segun los selecciones en la factura',
    'website': '',
    'depends': ['account',],
    'data': [

        'views/account_invoice_inherit_view.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,

}