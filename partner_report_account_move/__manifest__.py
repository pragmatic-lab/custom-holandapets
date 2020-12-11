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
    'name': 'Report Move Partner',
    'category': 'Report',
    'version': '12.0',
    'author': 'Brayhan Andres Jaramillo Castaño' ,
    'license': 'LGPL-3',
    'maintainer': 'brayhanjaramillo@hotmail.com',
    'website': '',
    'summary': """
            Módulo que permite sacar un reporte de todos los apuntes contables con una serie de filtros establecidos por el usuario

    """,
    'images': [],

    'description': """

        Módulo que permite sacar un reporte de todos los asientos contables y apuntes contables con una seria de filtros establecidos por el usuario


    """,
    
    'depends': [ 'account' , 'contacts'],

    'data': [
    
        'security/ir.model.access.csv',
        'views/account_partner_report_move_view.xml',
        'views/account_partner_report_move_view_.xml',
        'views/account_save_report_view.xml',
        'views/menu.xml',


    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}