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
	'name': 'Report Retro',
	'category': 'Report',
	'version': '12.0',
	'author': 'Brayhan Andres Jaramillo Castaño' ,
	'license': 'LGPL-3',
	'maintainer': 'brayhanjaramillo@hotmail.com',
	'website': '',
	'summary': '',
	'images': [],

	'description': """

	Módulo que permite modificar el estilo de los reportes en ventas y facturación, dandole de esta manera un diseño único.


	""",
	'depends': [ 'account', 'sale', 'web', 'l10n_co_res_partner', 'l10n_co_tax_extension'],

	'data': [
	
		'data/report_paperformat_data.xml',
		'report/report_invoice_document_inherit.xml',
		'report/report_assets_common_inherit.xml',
		'report/external_layout_retro.xml',
		'report/report_saleorder_document_inherit.xml',
		'views/update_company.xml'

	],


	'installable': True,
	'application': True,
	'auto_install': False,


}


