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


from odoo import models, fields, api, exceptions
from odoo.tools.translate import _
import re
import logging
_logger = logging.getLogger(__name__)
import csv
import os

class AccountAccountInherit(models.Model):

	_inherit = 'account.account'

	parent_id = fields.Many2one('account.account', 'Parent Account')
	child_ids = fields.One2many('account.account', 'parent_id', 'Children')

	def return_parent_cup(self, parent_code):
		"""
			Funcion que permite retornar el padre de la cuenta actual
		"""
		father_cup = ""

		if (len(parent_code) == 2):
			father_cup = parent_code[0:len(parent_code) - 1]

		elif (len(parent_code) % 2 == 0):
			father_cup = parent_code[0:len(parent_code) - 2]

		else:
			father_cup = parent_code[0:len(parent_code) - 1]

		return father_cup


	def search_record_cup(self, account_model, record_id, name_parent, user_type_id):

		if record_id:
			record_cup= account_model.search([('code', '=', record_id)])
			if record_cup:
				val_parent= self.return_parent_cup(record_id)
				if len(val_parent) > 0:
					record_cup_parent= account_model.search([('code', '=', val_parent)])
					if record_cup_parent:
						for x in record_cup:
							x.write({'parent_id': record_cup_parent.id})
			else:
				vals={'code': record_id, 'name': name_parent, 'user_type_id': user_type_id if user_type_id else None, 'company_id': 1, 'reconcile': True if user_type_id in ['1', '2'] else False}
				res= account_model.create(vals)
				val_parent= self.return_parent_cup(res.code)
				if len(val_parent) > 0:
					record_cup_parent= account_model.search([('code', '=', val_parent)])
					if record_cup_parent:
						for x in account_model.search([('code', '=', res.code)]):
							x.write({'parent_id': record_cup_parent.id})

	@api.model
	def load_data(self):

		account_ids = self.env['account.tax'].search([('refund_account_id', '!=', '')])

		data_ids=""
		for x in account_ids:
			data_ids+= str(x.id) + ","
		query_delete= """
					DELETE FROM account_account WHERE id not in (SELECT refund_account_id FROM account_tax WHERE refund_account_id > 0)"""
		#self.env.cr.execute(query_delete)

		data=[]
		data_father=[]
		account_model= self.env['account.account']

		dir_path = os.path.dirname(os.path.realpath(__file__))
		dir_path = dir_path[0: len(dir_path) - 6]
		dir_path = dir_path + "data/data.csv"

		with open(dir_path) as csvfile:
			reader = csv.DictReader(csvfile)
			for row in reader:

				vals={'code': row['code'], 'name': row['name'], 'user_type_id': row['user_type']}

				data.append(vals)

		for x in data:
			self.search_record_cup(account_model, x['code'], x['name'], x['user_type_id'])

		for x in account_model.search([]):
			self.search_record_cup(account_model, x.code, x.name, x.user_type_id)



	def create_data_account_group(self):
		"""
			Funcion que permite crear las cuentas en los grupos, estas se crean iguales a las cuentas
			que esten en el plan contable
		"""
		sql = """
			INSERT INTO account_group (
				name, 
				code_prefix
			)
			(SELECT 
				name,
			 	code
			FROM account_account
			ORDER BY code)
		"""
		self.env.cr.execute(sql)


	def search_parent_account_group(self, account_model, item):
		"""
			Funcion que permite asignar el padre a la cuenta del grupo
		"""
		if item:
			val_parent= self.return_parent_cup(item.code_prefix)
			if len(val_parent) > 0:
				record_cup_parent= account_model.search([('code_prefix', '=', val_parent)], limit=1)
				if record_cup_parent:
					item.write({'parent_id': record_cup_parent.id})

	@api.model
	def update_group_account(self):
		"""
			Funcion que permite asignar el grupo a la cuenta
		"""
		model_account_group = self.env['account.group']
		self.create_data_account_group()

		for x in model_account_group.search([]):
			self.search_parent_account_group(model_account_group, x)


	def search_parent_group(self, parent_id, model_account_group, item):
		"""
			Funcion que permite 
		"""
		if parent_id:
			account_group_id = model_account_group.search([('code_prefix', '=', parent_id)], limit=1)
			#se encontro el padre
			if account_group_id:
				item.write({'group_id': account_group_id.id})

			#no se encontro el padre
			else:
				pass

	@api.model
	def update_account_account_field_group(self):
		"""
			Funcion que permite asignar el grupo por cada cuenta del plan contable
		"""
		model_account_account = self.env['account.account']
		model_account_group = self.env['account.group']
		account_ids = model_account_account.search([])

		if account_ids:
			for x in account_ids:
				#si tiene padre
				if x.parent_id:
					code_parent = x.parent_id.code
					if code_parent:
						self.search_parent_group(code_parent, model_account_group, x)
				#si no tiene padre
				else:
					code = x.code
					if code:
						parent_id = self.return_parent_cup(code)
						if parent_id:
							self.search_parent_group(parent_id, model_account_group, x)

AccountAccountInherit()
