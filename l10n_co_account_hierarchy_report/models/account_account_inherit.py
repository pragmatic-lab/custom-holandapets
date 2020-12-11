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

from odoo import models, fields, api


class AccountAccountInherit(models.Model):
	_inherit = 'account.account'

	@api.depends('name', 'code', 'user_type_id', 'internal_type', 'reconcile')
	@api.multi
	def _compute_digitss(self):
		for account in self:
			account.level_account = len(str(account.code).strip()) 

	@api.depends('name', 'code', 'user_type_id', 'internal_type', 'reconcile')
	@api.multi
	def _compute_digits(self):
		for account in self:

			#Cuentas de nivel 1
			label_one = self.search([('level_account', '=', 1), ('code', '=', account.code[0])])
			name_one = ''
			if label_one and label_one.name:
				name_one = label_one and label_one.name
			else:
				name_one = self.search([('code', '=', account.code[0])], limit=1).name

			if name_one:
				account.one_digit = '%s %s' % (account.code[0], name_one or '')
			else:
				account.one_digit = ''


			#Cuentas nivel 2
			label_two = self.search([('level_account', '=', 2), ('code', '=', account.code[0:2])])
			name_two = ''
			if label_two and label_two.name:
				name_two = label_two and label_two.name
			else:
				name_two = self.search([('code', '=', account.code[0:2])], limit=1).name
			if name_two:
				account.two_digit = '%s %s' % (account.code[0:2], name_two or '')
			else:
				account.two_digit = ''


			#Cuentas nivel 4
			label_four = self.search([('level_account', '=', 4), ('code', '=', account.code[0:4])])
			name_four = ''
			if label_four and label_four.name:
				name_four = label_four and label_four.name
			else:
				name_four = self.search([('code', '=', account.code[0:4])], limit=1).name

			if name_four:
				account.four_digit = '%s %s' % (account.code[0:4], name_four or '')
			else:
				account.four_digit = ''

			#Cuentas nivel 6
			label_six = self.search([('level_account', '=', 6), ('code', '=', account.code[0:6])])
			name_six = ''
			if label_six and label_six.name:
				name_six = label_six and label_six.name
			else:
				name_six = self.search([('code', '=', account.code[0:6])], limit=1).name
			account.six_digit = '%s %s' % (account.code[0:6], name_six or '')


			#Cuentas nivel 8
			label_eight = self.search([('level_account', '=', 8), ('code', '=', account.code[0:8])])
			name_eight = ''
			if label_eight and label_eight.name:
				name_eight = label_eight and label_eight.name
			else:
				name_eight = self.search([('code', '=', account.code[0:8])], limit=1).name
			account.eight_digit = '%s %s' % (account.code[0:8], name_eight or '')


	level_account = fields.Char(string='Nivel Cuenta', compute='_compute_digitss', store=True, help="Nivel de la Cuenta")
	one_digit = fields.Char(string='1 Nivel', compute='_compute_digits', store=True, help="Cuenta Nivel 1")
	two_digit = fields.Char(string='2 Niveles', compute='_compute_digits', store=True, help="Cuenta Nivel 2")
	four_digit = fields.Char(string='4 Niveles', compute='_compute_digits', store=True, help="Cuenta Nivel 4")
	six_digit = fields.Char( string='6 Niveles', compute='_compute_digits', store=True, help="Cuenta Nivel 6")
	eight_digit = fields.Char(string='8 Niveles', compute='_compute_digits', store=True, help="Cuenta Nivel 8")
	
AccountAccountInherit()