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
    'name': 'Extractos Bancarios',
    'version': '12.0',
    'category': 'account',
    'author': 'Brayhan Andres Jaramillo Castaño',
    'summary': 'Modulo que permite validar el lista de las conciliaciones para que salgan las que estan disponibles para conciliar',
    'website': '',
    'depends': ['account',],
    'data': [

        'views/account_bank_statement_inherit.xml',

    ],
    'demo': [],
    'installable': True,
    'auto_install': False,

}