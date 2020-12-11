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

class AccountPartnerReportMove(models.TransientModel):
	_name = "account.partner_report_move"
	
	
	date_from = fields.Date(string="Fecha Inicio", default=fields.Date.context_today)
	date_to = fields.Date(string="Fecha Fin", default=fields.Date.context_today, required=True)
	partner_ids = fields.Many2many('res.partner', 'partner_report_move_res_partner_rel', column1='partner_report_move_id', column2="partner_id", string="Terceros")
	account_ids = fields.Many2many('account.account', 'report_account_ids_partner_report_move_rel', column1='partner_report_move_id', column2="account_id", string="Cuentas")
	save_report_id = fields.Many2one('account.save_report', string="Plantilla Cuentas")

	include_lines = fields.Boolean(string="Incluir Lineas")

	filename = fields.Char('Nombre Archivo')
	document = fields.Binary(string = 'Descargar Excel')

	@api.depends('save_report_id')
	@api.onchange('save_report_id')
	def onchange_save_report_id(self):
		if self.save_report_id:
			if self.save_report_id.account_ids:
				self.account_ids = self.upload_data_account_ids(self.save_report_id.account_ids)


	def upload_data_account_ids(self, account_ids):
		"""
			Funcion que permite retornar la data con el id de los hijos de las cuentas padres que seleccionaron
		"""
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


	def return_domain(self):
		"""
			Funcion que permite retornar un domonio con el cual se va hacer la filtro para la información
		"""
		domain= []

		#agregando fecha inicial
		if self.date_from:
			domain.append( ('date', '>=', str(self.date_from)) )

		#agregando fecha final
		if self.date_to:
			domain.append( ('date', '<=', str(self.date_to)) )

		#agregando terceros, si no selecciona ninguno va a incluir todos los terceros 
		if self.partner_ids:
			domain.append( ('partner_id', 'in', [x.id for x in self.partner_ids]) )
		else:
			#domain.append( ('partner_id', 'in', [x.id for x in self.env['res.partner'].search([('company_id', '=', self.env.user.company_id.id)])]) )
			pass
		#agrega las cuentas seleccionadas por el usuario, si no selecionada ninunga cuenta va a incluir todo el plan contable
		if self.account_ids:
			domain.append( ('account_id', 'in', [x.id for x in self.account_ids]) )
		else:
			#domain.append( ('account_id', 'in', [x.id for x in self.env['account.account'].search([('company_id', '=', self.env.user.company_id.id)])]) )
			pass
		domain.append( ('company_id', '=', self.env.user.company_id.id) )

		return domain


	def return_data_model(self):
		"""
			Funcion que se encarga de retornar la informacion necesaria para hacer el reporte
		"""

		domain = self.return_domain()
		print(domain)
		data = []
		model_partner_report = self.env['account.partner_report_move_view']
		if not self.include_lines:
			data = model_partner_report.read_group(domain, fields = ['debit', 'credit', 'account_id', 'partner_id'], groupby = ['partner_id', 'account_id', 'company_id'], lazy = False)

		print('la data es:')
		print(data)

		#print(self.env['account.move.line'].search(domain))
		"""
		[
		{'__count': 2, 'debit': 62492.52, 'credit': 0.0, 'partner_id': (1934, <odoo.tools.func.lazy object at 0x1119ef3f0>), 'account_id': (587, <odoo.tools.func.lazy object at 0x1119ef2d0>), 'company_id': (1, <odoo.tools.func.lazy object at 0x1119ef168>), '__domain': ['&', '&', '&', ('partner_id', '=', 1934), ('account_id', '=', 587), ('company_id', '=', 1), '&', '&', '&', ('date', '>=', '2020-05-21'), ('date', '<=', '2020-05-21'), ('partner_id', 'in', [1934]), ('account_id', 'in', [587, 634])]}, 
		{'__count': 10, 'debit': 328908.0, 'credit': 0.0, 'partner_id': (1934, <odoo.tools.func.lazy object at 0x1119ef3f0>), 'account_id': (634, <odoo.tools.func.lazy object at 0x1119ef288>), 'company_id': (1, <odoo.tools.func.lazy object at 0x1119ef168>), '__domain': ['&', '&', '&', ('partner_id', '=', 1934), ('account_id', '=', 634), ('company_id', '=', 1), '&', '&', '&', ('date', '>=', '2020-05-21'), ('date', '<=', '2020-05-21'), ('partner_id', 'in', [1934]), ('account_id', 'in', [587, 634])]}]
		"""

		return data


	def query_select_model(self):
		"""
			Funcion que permite realizar la creacion de los registros
		"""
		#data = self.return_data_model()
		#self.query_delete_model()

		sql = """

			SELECT
				partner.is_company AS is_company,
				aml.partner_id AS partner_id,
				--partner.doctype AS doctype,
				--partner.vat AS vat,
				--partner.first_surname AS first_name,
				--partner.second_name AS second_name,	
				--partner.first_surname AS first_surname,
				--partner.second_surname AS second_surname,
				partner.name AS name,
				partner.street AS street,
				partner.xidentification AS xidentification,
				--partner.street2 AS street2,	
				--rcs.code as state_id,
				--rc.code AS country_id,
				--rcc.code AS city_id,
				aml.account_id AS account_id,
				account.code AS account_code,
				account.name AS account_name,
				aml.credit AS credit,
				aml.debit AS debit,
				aml.balance AS balance,
				aml.move_id AS move_id,
				aml.id,
				aml.name AS name_aml,
				am.name AS name_am,
				aml.date AS date
				
			FROM account_move_line aml
				INNER JOIN account_account AS account
				ON (aml.account_id = account.id)
				
				INNER JOIN res_partner AS partner
				ON (aml.partner_id = partner.id)

				INNER JOIN account_move AS am
				ON (aml.move_id = am.id)

			"""

		sql += " WHERE aml.company_id = '" + str(self.env.user.company_id.id) + "' AND aml.date BETWEEN '" + str(self.date_from) + "' AND '" + str(self.date_to) + "' AND am.state = 'posted'  "
		#sql = sql + " WHERE aml.date BETWEEN '" + str(self.date_from) + "' AND '" + str(self.date_to) + "' "
		if self.partner_ids:
			partner_ids = ''
			for x in self.partner_ids:
				partner_ids += str(x.id) + "," 
			sql += "\n AND aml.partner_id IN (" + partner_ids[:len(partner_ids)-1] + ") "

		if self.account_ids:
			account_ids = ''
			for x in self.account_ids:
				account_ids += str(x.id) + "," 
			sql += "\n AND aml.account_id IN (" + account_ids[:len(account_ids)-1] + ") "

		self.env.cr.execute(sql)

		res = self.env.cr.dictfetchall()
		return res



	def query_select_model_group(self):
		"""
			Funcion que permite realizar la creacion de los registros
		"""
		#data = self.return_data_model()
		#self.query_delete_model()

		sql = """

			SELECT
				partner.is_company AS is_company,
				partner.id AS partner_id,
				--partner.doctype AS doctype,
				--partner.vat AS vat,
				--partner.first_surname AS first_name,
				--partner.second_name AS second_name,	
				--partner.first_surname AS first_surname,
				--partner.second_surname AS second_surname,
				partner.name AS name,
				partner.street AS street,
				partner.xidentification AS xidentification,
				--partner.street2 AS street2,
				account.id AS account_id,
				account.code AS account_code,
				account.name AS account_name,
				SUM(aml.credit) AS credit,
				SUM(aml.debit) AS debit,
				SUM(aml.balance) AS balance

			FROM  account_move_line aml
				INNER JOIN account_account AS account
				ON (aml.account_id = account.id)
				
				INNER JOIN res_partner AS partner
				ON (aml.partner_id = partner.id)

				INNER JOIN account_move AS am
				ON (aml.move_id = am.id)
				
			"""

		sql += " WHERE aml.company_id = '" + str(self.env.user.company_id.id) + "' AND aml.date BETWEEN '" + str(self.date_from) + "' AND '" + str(self.date_to) + "' AND am.state = 'posted'  "
		#sql = sql + " WHERE aml.date BETWEEN '" + str(self.date_from) + "' AND '" + str(self.date_to) + "' "
		if self.partner_ids:
			partner_ids = ''
			for x in self.partner_ids:
				partner_ids += str(x.id) + "," 
			sql += "\n AND aml.partner_id IN (" + partner_ids[:len(partner_ids)-1] + ") "

		if self.account_ids:
			account_ids = ''
			for x in self.account_ids:
				account_ids += str(x.id) + "," 
			sql += "\n AND aml.account_id IN (" + account_ids[:len(account_ids)-1] + ") "

		sql += "GROUP BY partner.id, account.id ORDER BY partner.name"

		self.env.cr.execute(sql)

		print(sql)

		res = self.env.cr.dictfetchall()
		return res




	def query_delete_model(self):
		"""
			Funcion que permite eliminar los registros del modelo
		"""
		sql_delete = """
			DELETE FROM account_partner_report_move_view;
		"""
		self.env.cr.execute(sql_delete)


	def return_type_document(self, document):
		"""
			Funcion que permite retornar el numero del documeto segun la Dian
		"""
		result = ''

		if document:
			if document == 'rut':
				result = '31'
			if document == 'national_citizen_id' or document == 'id_document':
				result = '13'
			if document == 'foreign_id_card':
				result = '22'
			if document == 'passport':
				result = '41'

		return result

	def return_data_load(self):

		return self.env['account.partner_report_move_view'].search([])

		
	def return_excel(self):
		"""
			Funcion que permite retornar la vista para descargar el excel
		"""
		return {
			'name': _(u'Resumen de Apuntes Contables'),
			'res_model':'account.partner_report_move',
			'type':'ir.actions.act_window',
			'view_type':'form',
			'view_mode':'form',
			'target':'new',
			'nodestroy': True,
			'res_id': self.id
		}



	def return_data_group(self):
		domain = self.return_domain()

		data = []
		model_partner_report = self.env['account.move.line']
		if not self.include_lines:
			data_account_ml = model_partner_report.read_group(domain, fields = ['debit', 'credit', 'account_id', 'partner_id'], groupby = ['partner_id', 'account_id', 'company_id'], lazy = False)
			data = data_account_ml



	@api.multi
	def generate_excel(self):
		"""
		Funcion que permite generar el excel
		"""

		data = []

		if not self.include_lines:
			data = self.query_select_model_group()
		else:
			data = self.query_select_model()

		format="%Y-%m-%d %H:%M:00"
		now=fields.Datetime.context_timestamp(self, fields.Datetime.from_string(fields.Datetime.now()))
		date_today=str(datetime.strftime(now, format))

		name_report = 'Resumen Apuntes Contables por Tercero' 

		Header_Text = name_report
		file_data = BytesIO()
		workbook = xlsxwriter.Workbook(file_data)
		worksheet = workbook.add_worksheet('F1001-19')

		#Formato de letras y celdas
		bold = workbook.add_format({'bold': 1,'align':'left','border':1, 'font_size': 14})
		format_tittle = workbook.add_format({'bold': 1,'align':'center', 'valign':'vcenter', 'border':1, 'fg_color':'#F9CEA9', 'font_size': 25 })
		letter_gray_name = workbook.add_format({'align':'left', 'font_color': 'gray', 'indent':2, 'font_size': 14})
		letter_gray = workbook.add_format({'align':'right', 'font_color': 'gray', 'num_format': '$#,#0.0', 'font_size': 14})
		letter_black_name = workbook.add_format({'align':'left', 'font_color': 'black', 'num_format': '$#', 'font_size': 14})
		letter_black = workbook.add_format({'align':'right', 'font_color': 'black', 'num_format': '$#', 'font_size': 14})
		header_format = workbook.add_format({'bold': 1,'align':'center','valign':'vcenter', 'border':1, 'fg_color':'#F9CEA9', 'font_size': 18 })

		bold_total = workbook.add_format({'align':'right', 'font_color': 'black', 'bold': 1, 'border':1, 'font_size': 14, 'num_format': '#'})
		bold_total_color = workbook.add_format({'align':'right', 'font_color': 'black', 'bold': 1, 'border':1, 'fg_color':'#F9CEA9', 'font_size': 18, 'num_format': '#'})




		worksheet.set_column('A1:A1',25)
		worksheet.set_column('B1:B1',45)
		worksheet.set_column('C1:C1',25)
		worksheet.set_column('D1:D1',55)
		worksheet.set_column('E1:E1',25)
		worksheet.set_column('F1:F1',55)
		worksheet.set_column('G1:G1',20)
		worksheet.set_column('H1:H1',20)
		worksheet.set_column('I1:I1',20)	






		if self.include_lines:
			worksheet.write('A1', "FECHA", header_format)
			worksheet.write('B1', "IDENTIFICACION", header_format)
			worksheet.write('C1', "TERCERO", header_format)
			worksheet.write('D1', "CODIGO", header_format)
			worksheet.write('E1', "CUENTA", header_format)
			worksheet.write('F1', "ASIENTO CONTABLE", header_format)
			worksheet.write('G1', "REFERENCIA", header_format)
			worksheet.write('H1', "DEBITO", header_format)
			worksheet.write('I1', "CREDITO", header_format)
			worksheet.write('J1', "BALANCE", header_format)
		else:

			worksheet.write('A1', "IDENTIFICACION", header_format)
			worksheet.write('B1', "TERCERO", header_format)
			worksheet.write('C1', "CODIGO", header_format)
			worksheet.write('D1', "CUENTA", header_format)
			worksheet.write('E1', "DEBITO", header_format)
			worksheet.write('F1', "CREDITO", header_format)
			worksheet.write('G1', "BALANCE", header_format)

		preview = name_report

		for i in range(1):

			row= 1
			col= 0

			#informacion de los medios de pagos
			if data:

				sum_credit = 0
				sum_debit = 0
				sum_balance = 0

				if self.include_lines:

					for x in data:

						worksheet.write(row,col, str(x['date']) or '', letter_black_name)
						worksheet.write(row,col+1, str(x['xidentification']) or '', letter_black_name)
						worksheet.write(row,col+2, str(x['name']) or '', letter_black_name)
						worksheet.write(row,col+3, x['account_code'], letter_black_name)
						worksheet.write(row,col+4, x['account_name'], letter_black_name)
						worksheet.write(row,col+5, x['name_am'], letter_black_name)
						worksheet.write(row,col+6, x['name_aml'], letter_black_name)
						worksheet.write(row,col+7, x['debit'] if x['debit'] else 0 , bold_total)
						worksheet.write(row,col+8, x['credit'] if x['credit'] else 0, bold_total)
						worksheet.write(row,col+9, x['balance'] if x['balance'] else 0, bold_total)
						sum_credit += x['credit']
						sum_debit += x['debit']
						sum_balance += x['balance']
						row+=1

					worksheet.write(row,col, '', header_format)
					worksheet.write(row,col+1, '', header_format)
					worksheet.write(row,col+2, '', header_format)
					worksheet.write(row,col+3, '', header_format)
					worksheet.write(row,col+4, '', header_format)
					worksheet.write(row,col+5, '', header_format)
					worksheet.write(row,col+6, 'TOTAL', header_format)
					worksheet.write(row,col+7, sum_debit, bold_total_color)
					worksheet.write(row,col+8, sum_credit, bold_total_color)
					worksheet.write(row,col+9, sum_balance or 0, bold_total_color)

				else:
					for x in data:

						worksheet.write(row,col, str(x['xidentification']) or '', letter_black_name)
						worksheet.write(row,col+1, str(x['name']) or '', letter_black_name)
						worksheet.write(row,col+2, x['account_code'], letter_black_name)
						worksheet.write(row,col+3, x['account_name'], letter_black_name)
						worksheet.write(row,col+4, x['debit'] if x['debit'] else 0 , bold_total)
						worksheet.write(row,col+5, x['credit'] if x['credit'] else 0, bold_total)
						worksheet.write(row,col+6, x['balance'] if x['balance'] else 0, bold_total)
						sum_credit += x['credit']
						sum_debit += x['debit']
						sum_balance += x['balance']
						row+=1

					worksheet.write(row,col, '', header_format)
					worksheet.write(row,col+1, '', header_format)
					worksheet.write(row,col+2, '', header_format)
					worksheet.write(row,col+3, 'TOTAL', header_format)
					worksheet.write(row,col+4, sum_debit, bold_total_color)
					worksheet.write(row,col+5, sum_credit, bold_total_color)
					worksheet.write(row,col+6, sum_balance or 0, bold_total_color)


		workbook.close()
		file_data.seek(0)

		self.write({'document':base64.encodestring(file_data.read()), 'filename':Header_Text + '  ' + str(self.date_from) + ' - ' + str(self.date_to) +'.xlsx'})

		return self.return_excel()





	def query_insert_model(self):
		"""
			Funcion que permite realizar la creacion de los registros
		"""
		#data = self.return_data_model()
		self.query_delete_model()

		sql = """
			INSERT INTO account_partner_report_move_view 
			(partner_id, 
			 --l10n_co_document_type, 
			 --vat, 
			 --first_name, 
			 --second_name, 
			 --first_surname, 
			 --second_surname, 
			 name, 
			 street, 
			 --street2, 
			 --state_id, 
			 --country_id,
			 --city_id,
			 account_id, 
			 credit, 
			 debit, 
			 balance,
			 account_move_id,
			 account_ml_id,
			 date
			 )

			(
			SELECT
				aml.partner_id AS partner_id,
				--partner.l10n_co_document_type AS l10n_co_document_type,
				--partner.vat AS vat,
				--partner.first_surname AS first_name,
				--partner.second_name AS second_name,	
				--partner.first_surname AS first_surname,
				--partner.second_surname AS second_surname,
				partner.name AS name,
				partner.street AS street,
				--partner.street2 AS street2,	
				--rcs.id as state_id,
				--rc.id AS country_id,
				--rcc.id AS city_id,
				aml.account_id AS account_id,
				aml.credit AS credit,
				aml.debit AS debit,
				aml.balance AS balance,
				aml.move_id,
				aml.id,
				aml.date
				
			FROM  account_move_line aml
				INNER JOIN account_account AS account
				ON (aml.account_id = account.id)
				
				INNER JOIN res_partner AS partner
				ON (aml.partner_id = partner.id)
				

			"""

		sql += " WHERE aml.company_id = " + str(self.env.user.company_id.id) + " AND aml.date BETWEEN '" + str(self.date_from) + "' AND '" + str(self.date_to) + "' "
		#sql = sql + " WHERE aml.date BETWEEN '" + str(self.date_from) + "' AND '" + str(self.date_to) + "' "
		if self.partner_ids:
			partner_ids = ''
			for x in self.partner_ids:
				partner_ids += str(x.id) + "," 
			sql += "\n AND aml.partner_id IN (" + partner_ids[:len(partner_ids)-1] + ") "

		if self.account_ids:
			account_ids = ''
			for x in self.account_ids:
				account_ids += str(x.id) + "," 
			sql += "\n AND aml.account_id IN (" + account_ids[:len(account_ids)-1] + ") "

		sql += ')'
		#print(sql)
		self.env.cr.execute(sql)


	@api.multi
	def generate_report_partner_move(self):
		"""
			Funcion que permite retornar la vista con los datos procesados
		"""

		self.return_data_group()
		self.query_insert_model()


		
		context = self.env.context.copy()
		context.update( { 'search_default_partner': True, 'search_default_account': True} ) 
		self.env.context = context


		return {
			'name': _(u'Resumen de Apuntes Contables'),
			'res_model':'account.partner_report_move_view',
			'type':'ir.actions.act_window',
			'view_mode': 'tree,form',
			'view_type': 'form',
			'context': context if not self.include_lines else None,
			#'domain': self.return_domain()
		}



	def _build_contexts(self, data):
		"""
			Funcion que permite construir un contexto con los filtros que se realizaron, como tambien agregando una data para el reporte
		"""
		result = {}
		result['date_from'] = data['form']['date_from'] or self.date_from
		result['date_to'] = data['form']['date_to'] or self.date_to
		result['partner_ids'] = data['form']['partner_ids'] or self.partner_ids
		result['account_ids'] = data['form']['account_ids'] or self.account_ids
		#result['info_data'] = self.return_data()

		return result

	def _print_report(self, data):
		"""
			Funcion que permite retornar el template del reporte
		"""
		return self.env.ref('summary_report_invoice.action_report_invoice_summary').with_context(landscape=True).report_action(self, data=data)

	"""
	@api.multi
	def generate_pdf(self):
		
			Funcion que permite generar el reporte pdf
		
		self.ensure_one()
		data = {}
		data['ids'] = self.env.context.get('active_ids', [])
		data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
		data['form'] = self.read(['date_from', 'date_to','user_ids', 'journal_ids'])[0]
		used_context = self._build_contexts(data)

		data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang'))
		return self.with_context(discard_logo_check=True)._print_report(data)
		"""


