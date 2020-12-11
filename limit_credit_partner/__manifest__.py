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
	'name': 'Limit Credit Partner',
	'category': 'Sale',
	'version': '12.0',
	'author': 'Brayhan Andres Jaramillo Castaño' ,
	'license': 'LGPL-3',
	'maintainer': 'brayhanjaramillo@hotmail.com',
	'website': '',
	'summary': '',
	'images': [],
	'description': """

		Permite restringir el credito del partner, como también bloquearlo de forma permanente

	""",
	'depends': [

	'sale', 'purchase', 'base', 'account', 'account_payment'

	],
	'data': [
		'security/sale_order_security.xml',
		'security/ir.model.access.csv',
		'views/sale_order_inherit_view.xml',
		'views/limit_credit_sequence.xml',
		'views/res_partner_inherit_view.xml',
		'views/limit_credit_partner_view.xml',
		'views/limit_credit_view.xml',
		'views/menu.xml'
	

	],


	'installable': True,
	'application': True,
	'auto_install': False,


}


