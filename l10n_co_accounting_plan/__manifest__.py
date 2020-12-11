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
    'name': 'Update Data Account',
    'version': '12.0',
    'category': 'Localization',
    'description': """
Use Chart of Account Hierarchy.
============================================

Usage:
-----------
- Add Parent Account at: Accounting > Adviser > Chart of Accounts > Parent Account

View:
--------
- Accounting > Adviser > Chart of Account Hierarchy

""",
    'author': 'Brayhan Andres Jaramillo Castaño',
    'depends': [ 'account'],

    'data': [
    
        'views/account_account_inherit_view.xml',
        'data/account_account_data.xml',


    ],
    'installable': True,
}
