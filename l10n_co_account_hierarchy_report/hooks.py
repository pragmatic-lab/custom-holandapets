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

from odoo import SUPERUSER_ID
from odoo.api import Environment


def post_init_hook(cr, pool):
	env = Environment(cr, SUPERUSER_ID, {})
	model_account = env['account.account']
	accounts = model_account.search([])

	for account in accounts:
		account.level_account = len(str(account.code).strip())

	for account in accounts:

		#Cuentas de nivel 1
		label_one = model_account.search([('level_account', '=', 1), ('code', '=', account.code[0])])
		name_one = ''
		if label_one and label_one.name:
			name_one = label_one and label_one.name
		else:
			name_one = model_account.search([('code', '=', account.code[0])], limit=1).name
		account.one_digit = '%s %s' % (account.code[0], name_one or '')


		#Cuentas nivel 2
		label_two = model_account.search([('level_account', '=', 2), ('code', '=', account.code[0:2])])
		name_two = ''
		if label_two and label_two.name:
			name_two = label_two and label_two.name
		else:
			name_two = model_account.search([('code', '=', account.code[0:2])], limit=1).name
		account.two_digit = '%s %s' % (account.code[0:2], name_two or '')


		#Cuentas nivel 4
		label_four = model_account.search([('level_account', '=', 4), ('code', '=', account.code[0:4])])
		name_four = ''
		if label_four and label_four.name:
			name_four = label_four and label_four.name
		else:
			name_four = model_account.search([('code', '=', account.code[0:4])], limit=1).name
		account.four_digit = '%s %s' % (account.code[0:4], name_four or '')


		#Cuentas nivel 6
		label_six = model_account.search([('level_account', '=', 6), ('code', '=', account.code[0:6])])
		name_six = ''
		if label_six and label_six.name:
			name_six = label_six and label_six.name
		else:
			name_six = model_account.search([('code', '=', account.code[0:6])], limit=1).name
		account.six_digit = '%s %s' % (account.code[0:6], name_six or '')


		#Cuentas nivel 8
		label_eight = model_account.search([('level_account', '=', 8), ('code', '=', account.code[0:8])])
		name_eight = ''
		if label_eight and label_eight.name:
			name_eight = label_eight and label_eight.name
		else:
			name_eight = model_account.search([('code', '=', account.code[0:8])], limit=1).name
		account.eight_digit = '%s %s' % (account.code[0:8], name_eight or '')