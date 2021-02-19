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

import logging
from odoo import api, fields, models, _
_logger = logging.getLogger(__name__)

import xlsxwriter
#from io import StringIO
from io import BytesIO
import base64

import time
from datetime import datetime, timedelta, date

import sys

class AccountInvoiceSummaryReport(models.TransientModel):
	_name = "account.invoice_summary_report"
	
	
	date_from = fields.Datetime(string='Fecha Inicio',default=lambda self: fields.datetime.now())
	date_to = fields.Datetime(string='Fecha Fin', default=lambda self: fields.datetime.now())
	#invoice_status = fields.Selection([('all', 'Todas'), ('paid', 'Pagadas'),('un_paid', 'Sin Pagar')], string='Estado de la Factura', default='all')
	user_ids = fields.Many2many(comodel_name='res.users', relation='account_invoice_summary_report_res_user_rel', column1='account_invoice_summary_report_id', column2='res_user_id', string='Responsable')
	journal_ids = fields.Many2many(comodel_name='account.journal', relation='account_invoice_summary_report_account_journal_rel', column1='account_invoice_summary_report_id', column2='journal_id', string=u'Métodos de Pago', domain="[('type', 'in', ['cash', 'bank'])]")
	type_report = fields.Selection( [('total_sale', 'Total Venta'), ('total_untaxes', 'Total Venta sin Impuesto'), ('total_inbound', 'Total Ingresos de Dinero'), ('total_expenses', 'Total Gastos')], string="Tipo Reporte", default='total_inbound', help=" (Total Venta) - Este tipo de reporte agrupa todas las cuentas 4. Como tambien las cuentas 2365, 2367, 2368, 2408. \n (Total Venta sin Impuesto) - Este tipo de reporte agrupa todas las cuentas 4. \n (Total Ingresos de Dinero) - Este tipo de reporte agrupa todas las cuentas 11. \n (Total Gastos) - Este reporte agrupa las cuentas 5, 6 y 7.")
	print_account =fields.Boolean('¿Imprimir Cuenta?')
	print_copy =fields.Boolean('¿Es Copia?')
	account_ids = fields.Many2many('account.account', 'report_account_ids_invoice_summary_report_rel', column1='summary_report_id', column2="account_id", string="Cuentas")
	print_account_ids = fields.Many2many('account.account', 'report_account_id_invoice_summary_report_print_rel', column1='summary_report_id', column2="account_id", string="Imprimir")

	filename = fields.Char('Nombre Archivo')
	document = fields.Binary(string = 'Descargar Excel')

	def returnHourFixed(self):
		if self.date_from and self.date_to:
			format="%Y-%m-%d %H:%M:00"
			date_from=fields.Datetime.context_timestamp(self, fields.Datetime.from_string(self.date_from))
			date_from=(datetime.strftime(date_from, format))
			date_to=fields.Datetime.context_timestamp(self, fields.Datetime.from_string(self.date_to))
			date_to=(datetime.strftime(date_to, format))


			return {'date_from': str(date_from), 'date_to': str(date_to)}

	def return_data_domain(self):
		"""
			Funcion que retorna el domain de los campos que fueron seleccionados en el wizard
		"""
		domain = []

		for wizard in self:
			
			date_from = wizard.date_from
			date_to = wizard.date_to

			domain.append(('date_move','>=',str(date_from)))
			domain.append(('date_move','<=',str(date_to)))

			if wizard.user_ids:
				domain.append(('user_id', 'in', [x.id for x in wizard.user_ids]))

			if wizard.journal_ids:
				domain.append(('journal_id', 'in', [x.id for x in wizard.journal_ids]))

			#_logger.info('este es el domain')
			#_logger.info(domain)
		return domain 

	def updateInfoBox(self, data, box_id, user_id):
		if data:
			for x in data:
				if x['box_id']==box_id:	
					new_user = []
					for user in x['users']:
						new_user.append(user)
					new_user.append(user_id)

					x['users'] = new_user

	def searchInfoBox(self, data, box_id, user_id):
		if data:
			for x in data:
				if x['box_id']==box_id:
					return True
		return False

	def returnInfoBox(self):
		"""
			Funcion que permite retornar los usuarios por caja
		"""
		box = []
		users = self.env['res.users'].search([])

		if users:
			for x in users:
				if x.box_id:
					if self.searchInfoBox(box, x.box_id.id, x.id) == False:
						box.append({'box_id': x.box_id.id, 'users': [x.id]})
					else:
						self.updateInfoBox(box, x.box_id.id, x.id)

		#print(box)
		return box

	def returnInfoBoxUser(self, box, user_id):
		if box:
			for x in box:
				if user_id in x['users']:
					return x
		return -1

	def search_sequence_invoice_initial_final(self, user_id):
		"""
			Funcion que permite obtener la secuencia inicial y final de las ventas realizadas
		"""
		initial = ''
		final = ''
		flag = False
		if user_id:

			box = self.returnInfoBox()
			
			data_box =self.returnInfoBoxUser(box, user_id)

			if data_box != -1:

				records = self.env['summary.payment_account_invoice'].search([('user_id', 'in', data_box['users'])], order='invoice_number asc')
				
				if records:
					for x in records:
					
						# if len(x.invoice_number) > 0:
						# 	if flag == False:
						# 		initial = str(x.invoice_number)
						# 		flag = True
						# 	final = str(x.invoice_number)

						if x.invoice_id.type == 'out_invoice':
							if flag == False:
								initial = str(x.invoice_number)
								flag = True
							final = str(x.invoice_number)
		return {
			'initial': initial,
			'final': final
		}




	@api.onchange('type_report')
	def onchange_type_report(self):
		model_account = self.env['account.account']
		if self.type_report:
			if self.type_report == 'total_sale':
				account_id = model_account.search([('code', '=', '4')], limit=1).id

				self.account_ids = [(6,_, [account_id])]
			

			if self.type_report == 'total_untaxes':
				account_id = model_account.search([('code', '=', '4')], limit=1).id
				if account_id:
					self.account_ids = [(6,_, [account_id])]
				

			if self.type_report == 'total_inbound':
				account_id = model_account.search([('code', '=', '11')], limit=1).id
				if account_id:
					self.account_ids = [(6,_, [account_id])]
				

			if self.type_report == 'total_expenses':
				account_ids = model_account.search([('code', 'in', ['5','6','7'])])
				if account_ids:
					self.account_ids = [(6,_, [x.id for x in account_ids])]
				
			self.onchange_parent_id()


	def upload_data_account_ids(self, account_ids):
		data=[]
		data_ids=[]

		if account_ids:


			sql_account_ids = ''
			for x in account_ids:
				sql_account_ids += " code LIKE '" + str(x.code) + "%' OR"
			
			sql = "SELECT id AS account_id FROM account_account WHERE "
			sql = sql + sql_account_ids[:len(sql_account_ids)-2]
			self.env.cr.execute(sql)
	
			res = self.env.cr.dictfetchall()

			children_ids = res

			if children_ids:
				for x in children_ids:
					data_ids.append(x['account_id'])
					
			data.append((6, 0, data_ids))
		
			return data

	@api.onchange('account_ids')
	def onchange_parent_id(self):

		if self.account_ids:
			self.print_account_ids= self.upload_data_account_ids(self.account_ids)


	def delete_records_model_summary_payment(self):
		"""
			Funcion que permite eliminar los registros del modelo
		"""
		sql_delete = """
			DELETE FROM summary_payment_account_invoice;
		"""
		self.env.cr.execute(sql_delete)


	@api.multi
	def execute_query_summary_payments(self):
		"""
			Funcion que permite crear los registros para el reporte
		"""
		if self.print_account_ids:
			
			date_from = self.date_from
			date_to = self.date_to
			data_user = [x.id for x in self.user_ids if self.user_ids]
			data_journal = [x.id for x in self.journal_ids if self.journal_ids]

			sql_info = {

			'date_from': date_from,
			'date_to': date_to,
			'data_user': str(str(data_user)[1:])[0:len(str(data_user)[1:])-1] ,
			'data_journal':  str(str(data_journal)[1:])[0:len(str(data_journal)[1:])-1],
			}
			
			sql = """
				INSERT INTO summary_payment_account_invoice (
					type_journal_name,
					invoice_id,
					number_authorization,
					payment_id,
					type_payment,
					user_id,
					payment_name,
					move_name,
					invoice_number,
					payment_ref,
					journal_id,
					journal_name,
					journal_type,
					partner_id,
					partner_name,
					account_id,
					account_name,
					aml_credit,
					aml_debit,
					balance,
					date_move,
					type_amount
					) 
					(
					SELECT
					journal.type_journal_name AS type_journal_name,
					(SELECT invoice_id
						FROM account_invoice_payment_rel
					WHERE payment_id = aml.payment_id) AS invoice_id,
					payment.number_authorization AS number_authorization,
					aml.payment_id AS payment_id,
					payment.payment_type AS type_payment,
					aml.create_uid AS user_id,
					aml.name AS payment_name,
					a_move.name AS move_name,
					substr(aml.ref,0, strpos(aml.ref, '/')) AS invoice_number,
					aml.ref AS payment_ref,
					aml.journal_id  AS journal_id,
					journal.name AS journal_name,
					journal.type AS journal_type,
					aml.partner_id AS partner_id,
					partner.name AS partner_name,
					aml.account_id AS account_id,
					( '[' || account.code || '] ' || account.name) AS account_name,
					aml.credit AS aml_credit,
					aml.debit AS aml_debit,
					aml.balance AS balance,
					(CASE WHEN extract(hour from (aml.create_date)) BETWEEN 0 AND 5 THEN (( a_move.date + '1 day'::interval) + aml.create_date::timestamp::time) ELSE (a_move.date + aml.create_date::timestamp::time)END) AS date_move,
					(CASE WHEN aml.credit = 0 THEN 'debit' ELSE 'credit' END) AS type_amount


					FROM account_move_line aml
						INNER JOIN account_account AS account
							ON (aml.account_id = account.id)

						INNER JOIN account_move AS a_move
							ON (aml.move_id = a_move.id)

						INNER JOIN account_journal AS journal
							ON (aml.journal_id = journal.id)

						INNER JOIN res_users AS aml_user
							ON (aml.create_uid = aml_user.id)

						LEFT JOIN res_partner AS partner
							ON (aml.partner_id = partner.id)

						LEFT JOIN account_payment as payment
							ON (aml.payment_id = payment.id)
				"""
			sql = sql + " WHERE ((CASE WHEN extract(hour from (aml.create_date)) BETWEEN 0 AND 5 THEN (( a_move.date + '1 day'::interval) + aml.create_date::timestamp::time) ELSE (a_move.date + aml.create_date::timestamp::time)END)) BETWEEN '" + str(date_from) + "' AND '" + str(date_to) +"' AND a_move.date BETWEEN '" + str(date_from) + "'::DATE AND '" + str(date_from) +"'::DATE  "
			
			data_account_ids = ''

			for x in self.print_account_ids:
				data_account_ids += str(x.id) + ','

			data_account_ids = data_account_ids[:len(data_account_ids)-1]

			sql = sql + " AND aml.account_id in (SELECT id FROM account_account WHERE id IN (" + data_account_ids + ")) "
			sql_data = ""

			if self.user_ids:
				user_ids = ''
				for x in data_user:
					user_ids += str(x) + "," 
				sql_data += "\n AND aml.create_uid IN (" + user_ids[:len(user_ids)-1] + ") "

			if self.journal_ids:
				journal_ids = ''
				for x in data_journal:
					journal_ids += str(x) + "," 
				sql_data += "\n AND aml.journal_id IN (" + journal_ids[:len(journal_ids)-1] + ") "


			sql_data += " ORDER BY aml.id ASC "
			sql_data += " )"

			sql = (sql + sql_data)

			#print('la sql es:')
			print(sql)
			
			self.delete_records_model_summary_payment()
			self.env.cr.execute(sql)


	def return_users_ids(self):
		"""
			Funcion que retorna los ids de los usuarios que hay en la consulta generada 
		"""
		sql = """
			SELECT 
				user_id
			FROM summary_payment_account_invoice
			GROUP BY user_id
		"""
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()
		data_user = []
		for x in res:
			data_user.append(x.get('user_id'))

		return data_user


	def return_data_user(self, user_ids):
		"""
			Funcion que permite retornar el id de los usuarios que fueron seleccionados
			o los usuarios que se encontraron en el reporte generado
		"""
		data_user_ids = self.return_users_ids()
		
		data_user = []

		if user_ids:
			data_user = user_ids

		else:
			data_user = data_user_ids

		return data_user


	def return_journals_ids(self):
		"""
			Funcion que retorna los ids de los diarios que hay en la consulta generada 
		"""
		sql = """
			SELECT 
				journal_id
			FROM summary_payment_account_invoice
			GROUP BY journal_id
		"""
		self.env.cr.execute(sql)
		data_journal = self.env.cr.dictfetchall()

		return data_journal


	def return_data_journal(self):
		"""
			Funcion que permite retornar el id de los diarios que fueron seleccionados
			o los diarios que se encontraron en el reporte generado
		"""
		data_journal_ids = self.return_journals_ids()
		data_journal = []
		for record in self:
			if record.journal_ids:
				data_journal = [x.id for x in self.journal_ids if self.journal_ids]

			if not record.journal_ids:
				data_journal = data_journal_ids
		return data_journal

	def return_id_name_user(self, user_ids):
		"""
			Permite retornar el id y el nombre del usuario
		"""

		data_user = self.return_data_user(user_ids)

		user_ids = ''
		if data_user:
			for x in data_user:
				user_ids += str(x) + ','
			sql = """
				SELECT 
					ru.id AS user_id, 
					partner.name AS name
				FROM res_users ru, res_partner partner
				WHERE ru.id in (%s)
				AND partner.id = ru.partner_id
			"""%(user_ids[:len(user_ids)-1])

			self.env.cr.execute(sql)
		
		res = self.env.cr.dictfetchall()
		return res

	def return_cartera(self, date_from, date_to, user_id):
		"""
			Funcion que permite retornar los registros los cuales no han sido cancelados en su totalidad
		"""
		sql = """
			SELECT 
				ai.create_date as date_move,
				rp.name AS partner_name,
				ai.number AS invoice_number,
				ai.amount_total AS amount_total,
				ai.residual AS amount_residual,
				am.name AS account_move
				
			FROM account_invoice ai, res_partner rp, account_move am

			WHERE 	ai.type = 'out_invoice'
					AND ai.state in ('open') 
					AND rp.id = ai.partner_id
					AND am.id = ai.move_id
					AND ai.create_date  BETWEEN '%s' AND '%s' 
			"""
			
		if user_id:
			sql = sql + "  AND ai.create_uid = %s"  

		sql = sql + " ORDER BY ai.number ASC"

		if user_id:
			sql = sql%(date_from, date_to, str(user_id) if user_id else None)
		else:
			sql = sql%(date_from, date_to)

		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()

		return res


	def return_data_detail_total(self, summary_report, user_id):
		"""
			Funcion que permite agrupar los medios de pago por usuario, mostrando la cantidad, el debito, el credito y el balance
		"""
		data = []

		data_detail_total = summary_report.sudo().read_group([('user_id', '=', user_id)], fields = [ 'journal_name', 'balance', 'aml_credit', 'aml_debit'], groupby = [u'user_id', 'journal_id', 'journal_name', ], lazy = False)
		
		if data_detail_total:
			#print('si hay algo')

			for x in data_detail_total:
				#print(x['journal_name'])
				vals = {
					'qty': x['__count'],
					'balance': x['balance'] or 0,
					'journal_name': x['journal_name'],
					'credit': x['aml_credit'] if x['aml_credit'] else 0,
					'debit': x['aml_debit'] or 0,
				}
				data.append(vals)

		return data

	def return_data_detail_total_type_journal(self, summary_report, user_id):
		"""
			Funcion que permite agrupar los medios de pago por usuario y tipo de diario, mostrando la cantidad, el debito, el credito y el balance
		"""
		data = []

		data_detail_total_type_journal = summary_report.sudo().read_group([('user_id', '=', user_id)], fields = [ 'journal_type', 'balance', 'aml_credit', 'aml_debit'], groupby = [u'user_id', 'journal_type'], lazy = False)
		
		if data_detail_total_type_journal:

			for x in data_detail_total_type_journal:
				vals = {
					'qty': x['__count'],
					'balance': x['balance'],
					'journal_type': self.return_name_type_journal(str(x['journal_type'])),
					'credit': x['aml_credit'],
					'debit': x['aml_debit'],
				}
				data.append(vals)

		return data

	def return_data_detail_total_type_journal_name(self, summary_report, user_id):
		"""
			Funcion que permite agrupar los medios de pago por usuario y tipo de diario, mostrando la cantidad, el debito, el credito y el balance
		"""
		data = []

		data_detail_total_type_journal = summary_report.sudo().read_group([('user_id', '=', user_id)], fields = [ 'type_journal_name', 'balance', 'aml_credit', 'aml_debit'], groupby = [u'user_id', 'type_journal_name'], lazy = False)
		
		if data_detail_total_type_journal:

			for x in data_detail_total_type_journal:

				vals = {
					'qty': x['__count'],
					'balance': x['balance'],
					'journal_type': self.return_name_type_journal_name(str(x['type_journal_name'])),
					'credit': x['aml_credit'],
					'debit': x['aml_debit'],
				}
				data.append(vals)

		return data

	def return_total_profit_and_lost(self, user_id, date_from, date_to):
		"""
			Permite calcular los gastos por usuario
		"""
		total_profit_and_lost = self.return_data_sql_record(" '5%'", user_id, date_from, date_to)
		return total_profit_and_lost


	def return_data_sql_record(self, data, user_id, date_from, date_to):
		"""
			Funcion que retorna las perdidas y ganancias 
		"""
		sql = """
				SELECT
					a_move.name AS name,
					aml.name AS description,
					product_tmpl.name AS product,
					aml.quantity as qty,
					partner.name AS partner_name,
					account.code || ' ' || account.name  AS account,
					(aml.balance) AS balance,
					aml.create_date AS date_move,
					journal.name AS journal_name,
					invoice.number AS invoice_number
				FROM account_move_line aml
					INNER JOIN account_account AS account
						ON (aml.account_id = account.id)

					INNER JOIN account_move AS a_move
						ON (aml.move_id = a_move.id)

					INNER JOIN account_journal AS journal
						ON (aml.journal_id = journal.id)

					INNER JOIN product_product AS pro
						ON (aml.product_id = pro.id)
						
					INNER JOIN product_template AS product_tmpl
						ON (pro.product_tmpl_id = product_tmpl.id)

					INNER JOIN res_users AS aml_user
						ON (aml.create_uid = aml_user.id)

					LEFT JOIN res_partner AS partner
						ON (aml.partner_id = partner.id)

					LEFT JOIN account_payment as payment
						ON (aml.payment_id = payment.id)

					LEFT JOIN account_invoice as invoice
						ON (aml.invoice_id = invoice.id)

			"""

		sql = sql + " WHERE aml.create_date BETWEEN '" + date_from + "' AND '" + date_to +"' "
		sql = sql + " AND aml.account_id in (SELECT id FROM account_account WHERE code LIKE " + data + ")"

		if '5' in data:
			sql += " AND journal.show_report_summary = true"
	
		if user_id:
			sql = sql + " AND aml.create_uid = " + str(user_id) 


		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()

		return res


	def return_taxes(self, company_id, date_from, date_to, validate, user_id):
		"""
			Funcion que permite retornar los impuestos para la impresion del reporte
		"""
		sql = ""
		if validate == 'out_invoice':
			sql = """
				SELECT 
					category.id AS category_id,
					category.name AS category,
					(CASE WHEN (tax.id ) IS NULL THEN -1 ELSE (tax.id) END) AS tax_id,
					(CASE WHEN (tax.name ) IS NULL THEN 'Sin Impuesto' ELSE (tax.name) END) AS name,
					sum(ai.discount) AS discount,
					sum(ail.price_total) AS total,
					sum(ail.price_subtotal_signed) AS total_neto,
					(sum(ail.price_total) - sum(ail.price_subtotal_signed)) AS total_taxes,
					(CASE WHEN (tax.type_tax_use ) IS NULL THEN 'Sin Impuesto' ELSE (tax.type_tax_use) END) AS type_tax
				FROM account_invoice_line ail
					INNER JOIN account_invoice AS ai
						ON (ail.invoice_id = ai.id)
					LEFT JOIN account_invoice_line_tax AS ailt
						ON (ail.id = ailt.invoice_line_id)
					LEFT JOIN account_tax AS tax
						ON (ailt.tax_id = tax.id)
					LEFT JOIN product_product AS product
						ON (ail.product_id = product.id)
					LEFT JOIN product_template AS product_template
						ON (product.product_tmpl_id = product_template.id)
					LEFT JOIN product_category AS category
						ON (product_template.categ_id = category.id)
				WHERE ai.date_invoice_complete BETWEEN '%s' AND '%s'
					AND ai.company_id = %s
					AND ai.type in ('%s')
					AND ai.state = 'paid'
				"""


		if validate == 'out_refund':
			sql = """
				SELECT 
					category.id AS category_id,
					category.name AS category,
					(CASE WHEN (tax.id ) IS NULL THEN -1 ELSE (tax.id) END) AS tax_id,
					(CASE WHEN (tax.name ) IS NULL THEN 'Sin Impuesto' ELSE (tax.name) END) AS name,
					sum(ai.discount) AS discount,
					sum(ail.price_total) AS total,
					sum(ail.price_subtotal_signed) AS total_neto,
					(sum(ail.price_total) - sum(ail.price_subtotal_signed)) AS total_taxes,
					(CASE WHEN (tax.type_tax_use ) IS NULL THEN 'Sin Impuesto' ELSE (tax.type_tax_use) END) AS type_tax
				FROM account_invoice_line ail
					INNER JOIN account_invoice AS ai
						ON (ail.invoice_id = ai.id)
					LEFT JOIN account_invoice_line_tax AS ailt
						ON (ail.id = ailt.invoice_line_id)
					LEFT JOIN account_tax AS tax
						ON (ailt.tax_id = tax.id)
					LEFT JOIN product_product AS product
						ON (ail.product_id = product.id)
					LEFT JOIN product_template AS product_template
						ON (product.product_tmpl_id = product_template.id)
					LEFT JOIN product_category AS category
						ON (product_template.categ_id = category.id)
				WHERE ai.date_invoice_complete BETWEEN '%s' AND '%s'
					AND ai.company_id = %s
					AND ai.type in ('%s')
					AND ai.state = 'paid'
				"""
			
		if user_id:
			sql = sql + " AND ail.create_uid = %s"  

		sql = sql + """

				GROUP BY tax.name, tax.type_tax_use, ai.type, category.name, tax.id, category.id
				ORDER BY tax.name

		"""

		if user_id:
			sql = sql%(date_from, date_to, company_id, validate, str(user_id) if user_id else None)
		else:
			sql = sql%(date_from, date_to, company_id, validate)
		_logger.info(sql)

		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()
		
		return res


	def search_value_data(self, data, item, type_column):
		"""
			Permite buscar si ya esta el mismo registro en la data
		"""
		if data:
			for x in data:
				if type_column == 'taxes':
					if x['tax_id']:
						if x['tax_id'] == item:
							return True
				if type_column == 'category':
					if x['category_id']:
						if x['category_id'] == item:
							return True
		return False


	def return_columns_taxes(self, data):
		"""
			Permite retornar las columas de los impuestos
		"""
		column_taxes = []
		if data:
			for x in data:
				if self.search_value_data(column_taxes, x['tax_id'], 'taxes') == False:
					column_taxes.append({'tax_id': x['tax_id'], 'tax_name': x['name']})

		return column_taxes

	def return_columns_category(self, data):
		"""
			Permite retornar las columas de las categorias
		"""
		column_categories = []
		if data:
			for x in data:
				if self.search_value_data(column_categories, x['category_id'], 'category') == False:
					column_categories.append({'category_id': x['category_id'], 'category': x['category']})

		return column_categories

	def return_items_columns(self, data, tax_id, category_id):
		result = filter(lambda x: ((x['category_id'] == category_id) and (x['tax_id'] == tax_id)), data) 	
		return list(result)

	def return_sum_total_categories_taxes(self, data, tax_id):
		result = filter(lambda x: ((x['tax_id'] == tax_id)), data) 	
		return list(result)
	"""
		Funciones para generar el excel
	"""
	def return_excel(self):
		"""
			Funcion que permite retornar la vista para descargar el excel
		"""
		return {
			'name': _(u'Resumen de Facturas'),
			'res_model':'account.invoice_summary_report',
			'type':'ir.actions.act_window',
			'view_type':'form',
			'view_mode':'form',
			'target':'new',
			'nodestroy': True,
			'res_id': self.id
		}

	def return_information_company(self):
		"""
			Esta funcion permite retornar los datos mas importantes de la compania para el reporte de excel
		"""
		company_id = self.env.user.company_id
		name = company_id.name
		nit = (company_id.partner_id.formatedNit or '')
		street = (company_id.street or '')
		email = (company_id.email or '')
		city = (company_id.partner_id.xcity.name or '')
		state = (company_id.partner_id.state_id.name or '')
		city_state = (state or '') + ' ' + (city or '')
		country_id = (company_id.country_id.name or '')
		phone = (company_id.phone or '')
		website = (company_id.website or '')

		vals = {
			'name': name,
			'nit': ('Nit: ' + nit) or '',
			'street': (street or '') + ' ' + (company_id.street2 or ''),
			'email': email or '',
			'city_state': city_state or '',
			'country_id': country_id or '',
			'phone': phone or '',
			'website': website or ''
		}

		return vals

	def return_data_outbound(self, x, user_id, data):
		"""
			Retorna la data con las respectivas devoluciones
		"""
		if x.type_payment == 'outbound':
			if x.invoice_id.origin:
				vals = {
					'date_move': x.date_move,
					'invoice_number': x.invoice_id.number,
					'payment_name': x.payment_name,
					'journal_name': x.journal_name,
					'origin': x.invoice_id.origin if x.invoice_id.origin else '',
					'partner_name': x.partner_name,
					'balance': x.balance
				}
				data.append(vals)

	def return_totals_columns(self, worksheet, row, bold_total, columns_categories_out_invoice, data_taxes_out_invoice, columns_taxes_out_invoice, size_column_taxes):
		"""
			Permite realizar la suma total de la tabla de doble entrada
		"""
		sum_total= 0
		sum_discount = 0
		sum_neto = 0
		worksheet.write(row, 0, 'TOTAL', bold_total)
		for x in columns_categories_out_invoice:
			
			col_data = 1
			
			for index in range(0, 1):
				data_new = self.return_items_columns(data_taxes_out_invoice, columns_taxes_out_invoice[index]['tax_id'], x['category_id'])
				
				if data_new:
					for index_data in data_new:
						sum_total += index_data['total']
						sum_discount += index_data['total'] - index_data['total_neto']
						sum_neto += index_data['total_neto']
						
		worksheet.write(row,col_data, (sum_total) or 0, bold_total)
		worksheet.write(row,col_data+1, (sum_discount) or 0, bold_total)
		worksheet.write(row,col_data+2, (sum_neto) or 0, bold_total)
		col_data +=3

		for val in range(1, size_column_taxes):
			sum_total= 0
			sum_discount = 0
			sum_neto = 0
			#print(columns_categories_out_invoice[val])

			for x in columns_categories_out_invoice:				
				data_new = self.return_items_columns(data_taxes_out_invoice, columns_taxes_out_invoice[val]['tax_id'], x['category_id'])
				#print(data_new)
				if data_new:
					for index_data in data_new:
						sum_total += index_data['total']
						sum_discount += index_data['total'] - index_data['total_neto']
						sum_neto += index_data['total_neto']

							
			worksheet.write(row,col_data, (sum_total) or 0, bold_total)
			worksheet.write(row,col_data+1, (sum_discount) or 0, bold_total)
			worksheet.write(row,col_data+2, (sum_neto) or 0, bold_total)
			col_data +=3
		row += 1

	def return_footer(self, worksheet, row, header_format, footer_format, header_center, value_box):
		"""
			Permite validar si el reporte es una copia o no
		"""
		row += 4
		if self.print_copy:
			col = 0
			worksheet.merge_range(row,col, row +1 ,col +6, ' *****     COPIA     *****', header_format)

		row+=3
		company_id = self.env.user.company_id
		col = 0
		worksheet.merge_range(row, col,row,col +6, '', footer_format)
		row+=1
		email = 'Correo: ' + str(company_id.email)
		website = 'Web: ' + str(company_id.website)
		worksheet.merge_range(row, col,row,col +6, email + '  ' + website, header_center)
		row+=1
		worksheet.merge_range(row, col,row,col +6, 'Comprobante de diario - Caja ' + value_box, header_center)


	def return_name_type_journal(self, type_journal):
		"""
			Permite retornar el nombre del tipo de diario
		"""
		value = ''
		if type_journal:
			if type_journal == 'bank':
				value = 'Banco'
			if type_journal == 'cash':
				value = 'Efectivo'
			if type_journal == 'sale':
				value = 'Venta'
			if type_journal == 'purchase':
				value = 'Compra'
			if type_journal == 'general':
				value = 'Miscelánea'
		return value

	def return_name_type_journal_name(self, type_journal):
		"""
			Permite retornar el nombre del tipo de diario
		"""
		value = ''
		if type_journal:
			if type_journal == 'card':
				value = 'Tarjetas'
			if type_journal == 'cash':
				value = 'Efectivo'
			if type_journal == 'transaction':
				value = 'Transacion'
			if type_journal == 'bonus':
				value = 'Bonos'
			if type_journal == 'others':
				value = 'Otros'
		return value

	def generate_header_excel(self, worksheet, name_report, user, user_id, bold, header_format, format_tittle):
		"""
			Funcion que permite generar el encabezado del informe de excel
		"""
		data_company = self.return_information_company()
		date_fixed = self.returnHourFixed()

		date_from_ = date_fixed['date_from']
		date_to_ = date_fixed['date_to']
		date_from = self.return_date_utc(self.date_from)
		date_to = self.return_date_utc(self.date_to)

		worksheet.set_column('A1:A1',35)
		worksheet.set_column('B1:B1',35)
		worksheet.set_column('C1:C1',35)
		worksheet.set_column('D1:C1',35)
		worksheet.set_column('E1:E1',40)
		worksheet.set_column('F1:F1',35)
		worksheet.set_column('G1:G1',35)
		worksheet.set_column('H1:H1',20)
		worksheet.set_column('I1:I1',20)
		worksheet.set_column('J1:J1',20)
		worksheet.set_column('K1:K1',20)
		worksheet.set_column('L1:L1',20)
		worksheet.set_column('M1:M1',20)
		worksheet.set_column('N1:N1',20)
		worksheet.set_column('O1:O1',20)
		worksheet.set_column('P1:P1',20)
		worksheet.set_column('Q1:Q1',20)
		worksheet.set_column('R1:R1',20)
		worksheet.set_column('S1:S1',20)

		for i in range(1):
			worksheet.write('A1', data_company['name'], bold)
			if data_company['nit']:
				worksheet.write('A2', data_company['nit'], bold)
			if data_company['street']:
				worksheet.write('A3', data_company['street'], bold)
			if data_company['phone']:
				worksheet.write('A4', data_company['phone'], bold)
			if data_company['city_state']:
				worksheet.write('A5', data_company['city_state'], bold)
			if data_company['country_id']:
				worksheet.write('A6', data_company['country_id'], bold)
			if data_company['email']:
				worksheet.write('A7', data_company['email'], bold)
			if data_company['website']:
				worksheet.write('A7', data_company['website'], bold)

			preview = name_report 
			worksheet.merge_range('C3:D4',preview, format_tittle)

			value_info_invoice = self.search_sequence_invoice_initial_final(user_id)
			data_dian = self.env['account.invoice'].search([], order='id desc', limit=1)

			box = self.env['res.users'].search([('id', '=', user_id)]).box_id

			value_box = ''
			if box:
				value_box = '[' + str(box.serial) +'] ' + str(box.name)


			worksheet.write('A9', "Cajero", header_format)
			worksheet.write('A10', user, bold)
			worksheet.write('B9', "Fecha Inical", header_format)
			worksheet.write('B10', str(date_from), bold)
			worksheet.write('C9', "Fecha Final", header_format)
			worksheet.write('C10', str(date_to), bold)
			worksheet.write('D9', "Autorizacion DIAN", header_format)
			worksheet.write('D10', data_dian.resolution_number, bold)
			worksheet.write('E9', "Fecha Autorizacion", header_format)
			worksheet.write('E10', str(data_dian.resolution_date) + ' - ' + str(data_dian.resolution_date_to), bold)
			worksheet.write('F9', "Rango de Facturacion", header_format)
			worksheet.write('F10', str(data_dian.resolution_number_from) + ' - ' + str(data_dian.resolution_number_to), bold)
			worksheet.write('G9', "CAJA", header_format)
			worksheet.write('G10', value_box, bold)			
			row=12
			col=0


			format="%Y-%m-%d %H:%M:00"
			now=fields.Datetime.context_timestamp(self, fields.Datetime.from_string(fields.Datetime.now()))
			date_today=str(datetime.strftime(now, format))
			date_create= str("Fecha Creacion")
			worksheet.write('G1', date_create, header_format)
			worksheet.write('G2', self.return_date_utc(date_today), bold)
			worksheet.write('G4', 'Consecutivo Inicial', header_format)
			worksheet.write('G5', value_info_invoice['initial'], bold)
			worksheet.write('G6', 'Consecutivo Final', header_format)
			worksheet.write('G7', value_info_invoice['final'], bold)

	def return_date_utc(self, date_begin):
		date_fix = date_begin - timedelta(hours=5)
		return date_fix

	def generate_body_excel(self, worksheet, user_id, model_spai, header_format, letter_black, bold_total, letter_black_name, bold_total_color, bold_total_gray, format_diag, header_format_subtitle, footer_format, header_center, value_box):
		"""
			Funcion que se encarga de armar el body completo del excel
		"""
		date_from = str(self.date_from)
		date_to = str(self.date_to)

		worksheet.write('A13', 'FECHA', header_format)
		worksheet.write('B13', 'FACTURA', header_format)
		worksheet.write('C13', 'REF. PAGO', header_format)
		worksheet.write('D13', 'AUTORIZACION', header_format)
		worksheet.write('E13', 'CLIENTE', header_format)
		worksheet.write('F13', 'VALOR', header_format)
		worksheet.write('G13', 'FORMA DE PAGO', header_format)

		row=13
		col=0


		sum_balance = 0

		data_refund = []
		data_profit_and_lost = self.return_total_profit_and_lost(user_id, date_from, date_to)
		data_detail_total = self.return_data_detail_total(model_spai, user_id)
		data_detail_total_type_journal = self.return_data_detail_total_type_journal(model_spai, user_id)
		data_detail_total_type_journal_name = self.return_data_detail_total_type_journal_name(model_spai, user_id) 
		
		data_taxes_out_invoice = self.return_taxes(self.env.user.company_id.id, date_from, date_to, 'out_invoice', user_id)
		columns_taxes_out_invoice = self.return_columns_taxes(data_taxes_out_invoice)
		columns_categories_out_invoice = self.return_columns_category(data_taxes_out_invoice)

		data_taxes_out_refund = self.return_taxes(self.env.user.company_id.id, date_from, date_to, 'out_refund', user_id)
		columns_taxes_out_refund = self.return_columns_taxes(data_taxes_out_refund)
		columns_categories_out_refund = self.return_columns_category(data_taxes_out_refund)

		#self.return_taxes(self.env.user.company_id.id, date_from, date_to, 'out_refund', user_id)
		#generando toda la data encontrada
		for x in model_spai.search([('user_id', '=', user_id)], order='invoice_number asc'):

			self.return_data_outbound(x, user_id, data_refund)

			if x.type_payment != 'outbound':
				date_fix = self.return_date_utc(x.date_move)
				worksheet.write(row,col , str(date_fix) or '', letter_black_name)
				worksheet.write(row,col+1 , x.invoice_id.number or '', letter_black_name)
				worksheet.write(row,col+2 , x.payment_ref or '', letter_black_name)
				worksheet.write(row,col+3 , x.number_authorization or '', letter_black_name)
				worksheet.write(row,col+4 , x.partner_name, letter_black_name)
				worksheet.write(row,col+5 , x.balance or 0, bold_total)
				worksheet.write(row,col+6 , x.journal_name, letter_black_name)

				sum_balance += x.balance or 0
				row+=1

		worksheet.write(row,col, '', letter_black_name)
		worksheet.write(row,col+1 , '', letter_black_name)
		worksheet.write(row,col+2 , '', letter_black_name)
		worksheet.write(row,col+3 , '', letter_black_name)
		worksheet.write(row,col+4 , 'Total', header_format)
		worksheet.write(row,col+5 , sum_balance, bold_total_color)
		worksheet.write(row,col+6 , '', letter_black_name)

		row+=2

		#agragando la cartera, son las facturas o registros que no estan pagos en su totalidad
		data_cartera = self.return_cartera(date_from, date_to, user_id)
		if data_cartera:
			worksheet.merge_range(row,col, row ,col +6, 'DETALLE DE CxC', header_format)
			row +=1
			worksheet.write(row,col , 'FECHA', header_format)
			worksheet.write(row,col+1 , 'FACTURA', header_format)
			worksheet.write(row,col+2 , 'ASIENTO CONTABLE', header_format)
			worksheet.write(row,col+3 , 'AUTORIZACION', header_format)
			worksheet.write(row,col+4 , 'CLIENTE', header_format)
			worksheet.write(row,col+5 , 'TOTAL', header_format)
			worksheet.write(row,col+6 , 'TOTAL ADEUDADO', header_format)
			row +=1

			sum_total_cartera = 0
			sum_total_residual = 0

			for x in data_cartera:
				date_fix = self.return_date_utc(x['date_move'])
				worksheet.write(row,col , str(date_fix) or '', letter_black_name)
				worksheet.write(row,col+1 , x['invoice_number'] or '', letter_black_name)
				worksheet.write(row,col+2 , x['account_move'] or '', letter_black_name)
				worksheet.write(row,col+3 , '', letter_black_name)
				worksheet.write(row,col+4 , x['partner_name'], letter_black_name)
				worksheet.write(row,col+5 , x['amount_total'] or 0, bold_total)
				worksheet.write(row,col+6 , x['amount_residual'], bold_total_gray)

				sum_total_cartera += x['amount_total']
				sum_total_residual += x['amount_residual']

				row +=1
			worksheet.write(row,col, '', letter_black_name)
			worksheet.write(row,col+1 , '', letter_black_name)
			worksheet.write(row,col+2 , '', letter_black_name)
			worksheet.write(row,col+3 , '', letter_black_name)
			worksheet.write(row,col+4 , 'Totales', header_format)
			worksheet.write(row,col+5 , sum_total_cartera, bold_total_color)
			worksheet.write(row,col+6 , sum_total_residual, bold_total_color)
			row +=1

		#agregando devoluciones
		if data_refund:
			row+=2
			worksheet.merge_range(row,col, row ,col +6, 'DEVOLUCIONES', header_format)
			row +=1
			worksheet.write(row,col , 'FECHA', header_format)
			worksheet.write(row,col+1 , 'DEVOLUCION', header_format)
			worksheet.write(row,col+2 , 'REF. PAGO', header_format)
			worksheet.write(row,col+3 , 'MEDIO DE PAGO', header_format)
			worksheet.write(row,col+4 , 'DOC. INICIAL', header_format)
			worksheet.write(row,col+5 , 'TERCERO', header_format)
			worksheet.write(row,col+6 , 'VALOR', header_format)

			row +=1

			sum_total_refund = 0
			#consultar account_invoice_payment_rel
			for x in data_refund:	
				date_fix = self.return_date_utc(x['date_move'])		
				worksheet.write(row,col , str(date_fix) or '', letter_black_name)
				worksheet.write(row,col+1 , x['invoice_number'] or '', letter_black_name)
				worksheet.write(row,col+2 , x['payment_name'] or '', letter_black_name)
				worksheet.write(row,col+3 , x['journal_name'], letter_black_name)
				worksheet.write(row,col+4 , x['origin'], letter_black_name)
				worksheet.write(row,col+5 , x['partner_name'] or 0, letter_black_name)
				worksheet.write(row,col+6 , x['balance'], bold_total_gray)

				sum_total_refund += x['balance']
				row +=1	

			worksheet.write(row,col, '', letter_black_name)
			worksheet.write(row,col+1 , '', letter_black_name)
			worksheet.write(row,col+2 , '', letter_black_name)
			worksheet.write(row,col+3 , '', letter_black_name)
			worksheet.write(row,col+4 , '', letter_black_name)
			worksheet.write(row,col+5 , 'Total', header_format)
			worksheet.write(row,col+6 , sum_total_refund, bold_total_color)
			row +=1




		#agregando gastos al reporte
		if model_spai.search([('user_id', '=', user_id)], order='invoice_number asc'):
			row+=2
			worksheet.merge_range(row,col, row ,col +6, 'GASTOS', header_format)
			row +=1
			worksheet.write(row,col , 'FECHA', header_format)
			worksheet.write(row,col+1 , 'FACTURA', header_format)
			worksheet.write(row,col+2 , 'DESCRIPCION', header_format)
			worksheet.write(row,col+3 , 'MEDIO DE PAGO', header_format)
			worksheet.write(row,col+4 , 'CUENTA', header_format)
			worksheet.write(row,col+5 , 'TERCERO', header_format)
			worksheet.write(row,col+6 , 'VALOR', header_format)
			row +=1

			sum_total_profit_and_lost = 0
			#consultar account_invoice_payment_rel

			for x in model_spai.search([('user_id', '=', user_id)], order='invoice_number asc'):
				
				if x.invoice_id.type == 'in_invoice':
					date_fix = self.return_date_utc(x.date_move)
					worksheet.write(row,col , str(date_fix) or '', letter_black_name)
					worksheet.write(row,col+1 , x.invoice_id.number or '', letter_black_name)
					worksheet.write(row,col+2 , x.payment_name or '', letter_black_name)
					worksheet.write(row,col+3 , x.journal_id.name or '', letter_black_name)
					worksheet.write(row,col+4 , x.account_name, letter_black_name)
					worksheet.write(row,col+5 , x.partner_id.name or 0, letter_black_name)
					worksheet.write(row,col+6 , x.balance, bold_total_gray)


					sum_total_profit_and_lost += x.balance
					row +=1

				if not x.invoice_id and x.type_payment == 'outbound':
					date_fix = self.return_date_utc(x.date_move)
					worksheet.write(row,col , str(date_fix) or '', letter_black_name)
					worksheet.write(row,col+1 , x.invoice_id.number or '', letter_black_name)
					worksheet.write(row,col+2 , x.payment_name or '', letter_black_name)
					worksheet.write(row,col+3 , x.journal_id.name or '', letter_black_name)
					worksheet.write(row,col+4 , x.account_name, letter_black_name)
					worksheet.write(row,col+5 , x.partner_id.name or 0, letter_black_name)
					worksheet.write(row,col+6 , x.balance, bold_total_gray)


					sum_total_profit_and_lost += x.balance
					row +=1

			# for x in data_profit_and_lost:	

			# 	worksheet.write(row,col , str(x['date_move']) or '', letter_black_name)
			# 	worksheet.write(row,col+1 , x['invoice_number'] or '', letter_black_name)
			# 	worksheet.write(row,col+2 , x['description'], letter_black_name)
			# 	worksheet.write(row,col+3 , x['journal_name'], letter_black_name)
			# 	worksheet.write(row,col+4 , x['account'], letter_black_name)
			# 	worksheet.write(row,col+5 , x['partner_name'] or 0, letter_black_name)
			# 	worksheet.write(row,col+6 , x['balance'], bold_total_gray)


			# 	sum_total_profit_and_lost += x['balance']
			# 	row +=1	
			worksheet.write(row,col, '', letter_black_name)
			worksheet.write(row,col+1 , '', letter_black_name)
			worksheet.write(row,col+2 , '', letter_black_name)
			worksheet.write(row,col+3 , '', letter_black_name)
			worksheet.write(row,col+4 , '', letter_black_name)
			worksheet.write(row,col+5 , 'Total', header_format)
			worksheet.write(row,col+6 , sum_total_profit_and_lost, bold_total_color)
			row +=1

		#agregando detalle de medios de pagos
		if data_detail_total:
			row+=2
			worksheet.merge_range(row,col, row ,col +4, 'DETALLES DE MEDIOS DE PAGO', header_format)
			row +=1
			worksheet.write(row,col , 'MEDIO DE PAGO', header_format)
			worksheet.write(row,col+1 , 'CTIDAD PAGOS', header_format)
			worksheet.write(row,col+2 , 'DEBITO', header_format)
			worksheet.write(row,col+3 , 'CREDITO', header_format)
			worksheet.write(row,col+4 , 'TOTAL DINERO', header_format)
			row +=1

			sum_qty = 0
			sum_debit = 0
			sum_credit = 0
			sum_balance = 0

			for x in data_detail_total:			
				worksheet.write(row,col , str(x['journal_name']) or '', letter_black_name)
				worksheet.write(row,col+1 , x['qty'] or '', bold_total)
				worksheet.write(row,col+2 , x['debit'], bold_total)
				worksheet.write(row,col+3 , x['credit'], bold_total)
				worksheet.write(row,col+4 , x['balance'], bold_total_gray)

				sum_qty += x['qty']
				sum_debit += x['debit']
				sum_credit += x['credit']
				sum_balance += x['balance']

				row +=1	
			worksheet.write(row,col, 'Total', header_format)
			worksheet.write(row,col+1 , sum_qty or 0, bold_total_color)
			worksheet.write(row,col+2 , sum_debit or 0, bold_total_color)
			worksheet.write(row,col+3 , sum_credit or 0, bold_total_color)
			worksheet.write(row,col+4 , sum_balance or 0, bold_total_color)
			row +=1


		#agregando detalle de medios de pagos por tipo de diario
		if data_detail_total_type_journal_name:
			row+=2
			worksheet.merge_range(row,col, row ,col +4, 'TOTAL MEDIOS DE PAGO', header_format)
			row +=1
			worksheet.write(row,col , 'TIPO DINERO INGRESADO', header_format)
			worksheet.write(row,col+1 , 'CTIDAD PAGOS', header_format)
			worksheet.write(row,col+2 , 'INGRESOS', header_format)
			worksheet.write(row,col+3 , 'EGRESOS', header_format)
			worksheet.write(row,col+4 , 'DISPONIBLE', header_format)
			row +=1

			sum_qty = 0
			sum_debit = 0
			sum_credit = 0
			sum_balance = 0

			for x in data_detail_total_type_journal_name:			
				worksheet.write(row,col , x['journal_type'] or '', letter_black_name)
				worksheet.write(row,col+1 , x['qty'] or '', bold_total)
				worksheet.write(row,col+2 , x['debit'], bold_total)
				worksheet.write(row,col+3 , x['credit'], bold_total)
				worksheet.write(row,col+4 , x['balance'], bold_total_gray)

				sum_qty += x['qty']
				sum_debit += x['debit']
				sum_credit += x['credit']
				sum_balance += x['balance']

				row +=1	
			worksheet.write(row,col, 'Total', header_format)
			worksheet.write(row,col+1 , sum_qty or 0, bold_total_color)
			worksheet.write(row,col+2 , sum_debit or 0, bold_total_color)
			worksheet.write(row,col+3 , sum_credit or 0, bold_total_color)
			worksheet.write(row,col+4 , sum_balance or 0, bold_total_color)
			row +=1



		#agregando inventario de cajas
		if data_detail_total_type_journal:
			row+=2
			worksheet.merge_range(row,col, row ,col +3, 'INVENTARIO DE CAJAS', header_format)
			row +=1
			worksheet.write(row,col , 'CAJA', header_format)
			worksheet.write(row,col+1 , 'SERIAL', header_format)
			worksheet.write(row,col+2 , 'SEDE', header_format)
			worksheet.write(row,col+3 , 'NUMERACION', header_format)
			row +=1

			worksheet.write(row,col, 'CAJA PPAL NORTE', letter_black_name)
			worksheet.write(row,col+1 , '987654321' or 0, letter_black_name)
			worksheet.write(row,col+2 , 'NORTE' or 0, letter_black_name)
			worksheet.write(row,col+3 , '1' or 0, letter_black_name)
			row +=1
			worksheet.write(row,col, 'CAJA AUXILIAR GASTOS NORTE', letter_black_name)
			worksheet.write(row,col+1 , '' or 0, letter_black_name)
			worksheet.write(row,col+2 , 'NORTE' or 0, letter_black_name)
			worksheet.write(row,col+3 , '2' or 0, letter_black_name)
			row +=1
			worksheet.write(row,col, 'CAJA PPAL SUR', letter_black_name)
			worksheet.write(row,col+1 , '123456789' or 0, letter_black_name)
			worksheet.write(row,col+2 , 'SUR' or 0, letter_black_name)
			worksheet.write(row,col+3 , '1' or 0, letter_black_name)
			row +=1

		if columns_taxes_out_invoice and columns_categories_out_invoice:
			
			size_column_taxes = len(columns_taxes_out_invoice)
			row+=2
			worksheet.merge_range(row,col, row, col+ len(columns_taxes_out_invoice)*3, 'RESUMEN DE VENTAS', header_format)
			row+=1
			worksheet.write(row,col, 'OPERACIONES', bold_total_color)
			worksheet.write(row+1,col, 'CATEGORIA', format_diag)
			col_initial = 1
			col_final = 3
			col_fijo = 1
			for x in columns_taxes_out_invoice:

				worksheet.merge_range(row,col_initial, row,col_final, str(x['tax_name']), header_format)
				col_initial=col_final +1
				col_final=col_initial + 2

				worksheet.write(row+1,col_fijo, 'VALOR', header_format_subtitle)
				worksheet.write(row+1,col_fijo+1, 'IMPUESTO', header_format_subtitle)
				worksheet.write(row+1,col_fijo+2, 'BASE', header_format_subtitle)
				col_fijo+=3

			row +=2
			for x in columns_categories_out_invoice:
				worksheet.write(row,col, str(x['category']), header_format_subtitle)
				col_data = 1
				for index in range(0, size_column_taxes):
					data_new = self.return_items_columns(data_taxes_out_invoice, columns_taxes_out_invoice[index]['tax_id'], x['category_id'])

					if data_new:
						for index_data in data_new:
							worksheet.write(row,col_data, (index_data['total']) or 0, bold_total)
							worksheet.write(row,col_data+1, (index_data['total'] - index_data['total_neto']) or 0, bold_total)
							worksheet.write(row,col_data+2, (index_data['total_neto']) or 0, bold_total)
							
							col_data+=3
					else:
						worksheet.write(row,col_data, 0, bold_total)
						worksheet.write(row,col_data+1, 0, bold_total)
						worksheet.write(row,col_data+2, 0, bold_total)
						col_data+=3

				row +=1

			self.return_totals_columns(worksheet, row, bold_total_color, columns_categories_out_invoice, data_taxes_out_invoice, columns_taxes_out_invoice, size_column_taxes)

		if columns_taxes_out_refund and columns_categories_out_refund:

			size_column_taxes = len(columns_taxes_out_refund)
			row+=3
			worksheet.merge_range(row,col, row, col+ len(columns_taxes_out_refund)*3, 'RESUMEN DE VENTAS (DEVOLUCIONES)', header_format)
			row+=1
			worksheet.write(row,col, 'OPERACIONES', bold_total_color)
			worksheet.write(row+1,col, 'CATEGORIA', format_diag)
			col_initial = 1
			col_final = 3
			col_fijo = 1
			for x in columns_taxes_out_refund:

				worksheet.merge_range(row,col_initial, row,col_final, str(x['tax_name']), header_format)
				col_initial=col_final +1
				col_final=col_initial + 2

				worksheet.write(row+1,col_fijo, 'VALOR', header_format_subtitle)
				worksheet.write(row+1,col_fijo+1, 'IMPUESTO', header_format_subtitle)
				worksheet.write(row+1,col_fijo+2, 'BASE', header_format_subtitle)
				col_fijo+=3

			row +=2
			sum_total = 0
			sum_discount = 0
			row_initial = row
			for x in columns_categories_out_refund:
				worksheet.write(row,col, str(x['category']), header_format_subtitle)
				col_data = 1

		
				for index in range(0, size_column_taxes):
					
					data_new = self.return_items_columns(data_taxes_out_refund, columns_taxes_out_refund[index]['tax_id'], x['category_id'])
					
					if data_new:
						for index_data in data_new:
							worksheet.write(row,col_data, (index_data['total']) or 0, bold_total)
							worksheet.write(row,col_data+1, (index_data['total'] - index_data['total_neto']) or 0, bold_total)
							worksheet.write(row,col_data+2, (index_data['total_neto']) or 0, bold_total)

							col_data+=3

					else:
						worksheet.write(row,col_data, 0, bold_total)
						worksheet.write(row,col_data+1, 0, bold_total)
						worksheet.write(row,col_data+2, 0, bold_total)
						col_data+=3

					
				row +=1
			self.return_totals_columns(worksheet, row, bold_total_color, columns_categories_out_refund, data_taxes_out_refund, columns_taxes_out_refund, size_column_taxes)

		self.return_footer(worksheet, row, header_format, footer_format, header_center, value_box)
			

	def generate_data_complete_excel(self, worksheet, name_report, user_id, user_name, model_spai, bold, header_format, format_tittle, letter_black, bold_total, letter_black_name, bold_total_color, bold_total_gray, format_diag, header_format_subtitle, footer_format, header_center, value_box):
		"""
			Permite generar el excel completo
			header
			body
		"""
		self.generate_header_excel(worksheet, name_report, user_name, user_id, bold,  header_format, format_tittle)
		self.generate_body_excel(worksheet, user_id, model_spai, header_format, letter_black, bold_total, letter_black_name, bold_total_color, bold_total_gray, format_diag, header_format_subtitle, footer_format, header_center, value_box)

	@api.multi
	def generate_excel(self):
		"""
		Funcion que permite generar el excel
		"""
		self.execute_query_summary_payments()
		data_user = self.return_id_name_user([x.id for x in self.user_ids if self.user_ids])

		model_spai = self.env['summary.payment_account_invoice']

		format="%Y-%m-%d %H:%M:00"
		now=fields.Datetime.context_timestamp(self, fields.Datetime.from_string(fields.Datetime.now()))
		date_today=str(datetime.strftime(now, format))

		
		name_report = 'Comprobante de Informe Diario' 

		Header_Text = name_report
		file_data = BytesIO()
		workbook = xlsxwriter.Workbook(file_data)
		

		#Formato de letras y celdas
		bold = workbook.add_format({'bold': 1,'align':'left','border':1, 'font_size': 14})
		format_tittle = workbook.add_format({'bold': 1,'align':'center', 'valign':'vcenter', 'border':1, 'fg_color':'#F9CEA9', 'font_size': 25 })
		letter_gray_name = workbook.add_format({'align':'left', 'font_color': 'gray', 'indent':2, 'font_size': 14})
		letter_gray = workbook.add_format({'align':'right', 'font_color': 'gray', 'num_format': '$#,#0.0', 'font_size': 14})
		letter_black_name = workbook.add_format({'align':'left', 'font_color': 'black', 'num_format': '$#', 'font_size': 14})
		letter_black = workbook.add_format({'align':'right', 'font_color': 'black', 'num_format': '$#', 'font_size': 14})
		header_format = workbook.add_format({'bold': 1,'align':'center','valign':'vcenter', 'border':1, 'fg_color':'#F9CEA9', 'font_size': 18 })
		header_format_subtitle = workbook.add_format({'bold': 1,'align':'center','valign':'vcenter', 'border':1, 'fg_color':'#F9E9DB', 'font_size': 18 })
		footer_format = workbook.add_format({'bold': 1,'align':'center','valign':'vcenter', 'border':10,  'font_size': 18, 'bottom':1, 'top':0, 'right':0, 'left':0})
		header_center = workbook.add_format({'bold': 1,'align':'center','valign':'vcenter', 'font_size': 15 })
		

		bold_total = workbook.add_format({'align':'right', 'font_color': 'black', 'bold': 1, 'border':1, 'font_size': 14, 'num_format': '$#,#0.0'})
		bold_total_color = workbook.add_format({'align':'right', 'font_color': 'black', 'bold': 1, 'border':1, 'fg_color':'#E3E4E5', 'font_size': 18, 'fg_color':'#F9CEA9', 'num_format': '$#,#0.0'})
		bold_total_gray = workbook.add_format({'align':'right', 'font_color': 'black', 'bold': 1, 'border':1, 'fg_color':'#E3E4E5', 'font_size': 14, 'num_format': '$#,#0.0'})
		format_diag = workbook.add_format({'align':'left', 'font_color': 'black', 'bold': 1, 'fg_color':'#E3E4E5', 'font_size': 18, 'fg_color':'#F9CEA9'})
		
		size_user = len(data_user)
		iterator_user = 1

		for x in data_user:
			worksheet = workbook.add_worksheet(str(x['name']) or 'Boot')

			box = self.env['res.users'].search([('id', '=', x['user_id'])]).box_id

			value_box = ''
			if box:
				value_box = str(box.name)
			value_box += '  ' + ' Pagina ' + str(iterator_user) + '/' + str(size_user)
			

			self.generate_data_complete_excel(worksheet, name_report, x['user_id'], x['name'], model_spai, bold, header_format, format_tittle, letter_black, bold_total, letter_black_name, bold_total_color, bold_total_gray, format_diag, header_format_subtitle, footer_format, header_center, value_box)
			iterator_user+=1
		workbook.close()
		file_data.seek(0)

		date_from_ = self.date_from
		date_to_ = self.date_to
		self.write({'document':base64.encodestring(file_data.read()), 'filename':Header_Text + '  ' + str(self.return_date_utc(date_from_)) + ' - ' + str(self.return_date_utc(date_to_)) +'.xlsx'})


		return self.return_excel()


	"""
		Funciones para generar el excel
	"""
	def _build_contexts(self, data):
		"""
			Funcion que permite construir un contexto con los filtros que se realizaron, como tambien agregando una data para el reporte
		"""


		result = {}
		result['date_from'] =  str(self.date_from)
		result['date_to'] =  self.date_to
		result['print_copy'] =  self.print_copy
		result['user_ids'] = [x.id for x in self.user_ids if self.user_ids] or None
		result['journal_ids'] = data['form']['journal_ids'] or self.journal_ids
		#result['info_data'] = self.return_data()

		#print(result)
		return result

	def _print_report(self, data):
		"""
			Funcion que permite retornar el template del reporte
		"""
		return self.env.ref('summary_report_invoice.action_report_invoice_summary').with_context(landscape=True).report_action(self, data=data)

	@api.multi
	def generate_pdf(self):
		"""
			Funcion que permite generar el reporte pdf general del dia
		"""
		self.ensure_one()
		self.execute_query_summary_payments()

		data = {}
		data['ids'] = self.env.context.get('active_ids', [])
		data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
		data['form'] = self.read(['date_from', 'date_to','user_ids', 'journal_ids'])[0]
		used_context = self._build_contexts(data)

		#data['form']['doctor_attention_ids'] = [x for x in self.doctor_attention_ids]
		data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang'))

		return self.with_context(discard_logo_check=True)._print_report(data)


	"""
		Genera la vista tree
	"""
	@api.multi
	def return_view_tree_summary_payments(self):
		"""
			Funcion que permite retornar la vista con los datos procesados
		"""

		self.execute_query_summary_payments()
		context = self.env.context.copy()
		context.update( {  'search_default_user': True, 'search_default_journal': True, 'search_default_type_invoice_general': True} ) 
		self.env.context = context

		return {
			'name': _('Resumen de Pagos'),
			'res_model':'summary.payment_account_invoice',
			'type':'ir.actions.act_window',
			'view_mode': 'tree,form',
			'view_type': 'form',
			'context': context
		}

	@api.multi
	def generate_view_summary(self):
		return self.return_view_tree_summary_payments()

AccountInvoiceSummaryReport()