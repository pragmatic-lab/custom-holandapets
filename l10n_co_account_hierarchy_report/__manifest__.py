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
    'name': "Account Hierarchy Report",
    'version': "12.0",
    'summary': "Account Hierarchy Report",
    'category': "Accounting",
    'author': "Brayhan Andres Jaramillio Castano",
    'license': "AGPL-3",
    'images': [
    ],
    'depends': [
        "account",
    ],
    'data': [
        "security/ir.model.access.csv",
        "views/account_account_inherit_view.xml",
        "report/account_hierarchy_report_pivot.xml",
        'report/report_puc_hierarchy.xml',
        'views/hierarchy_report_print_view.xml',
        'views/menu.xml'
    ],
    'qweb': [
        'static/src/xml/*.xml'
    ],
    #'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
}