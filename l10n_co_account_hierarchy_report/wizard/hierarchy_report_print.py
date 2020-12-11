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
from odoo import models, fields, api, _
import logging
from odoo import api, fields, models, _
_logger = logging.getLogger(__name__)

import xlsxwriter
from io import BytesIO
import base64

import time
from datetime import datetime, timedelta, date
import sys
from odoo.exceptions import UserError
from functools import reduce

class HierarchyReportPrint(models.TransientModel):
	_name = 'hierarchy.report_print'
	_desription = "wizard allow to show the account level"

	# ACCOUNT_LEVEL = [ ('level_one', 'Nivel 1'),
	# 				('level_two', 'Nivel 2'),
	# 				('level_four', 'Nivel 4'),
	# 				('level_six', 'Nivel 6'),
	# 				('level_eight', 'Nivel 8')]

	ACCOUNT_LEVEL = [ ('1', 'Nivel 1'),
					('2', 'Nivel 2'),
					('4', 'Nivel 4'),
					('6', 'Nivel 6'),
					('8', 'Nivel 8'),
					('10', 'Nivel 10'),]

	GENERATION = [ ('balance', 'Balance'),
					('state', 'Estado') ]

	date_from = fields.Date(string='Fecha Inicio', required=True)
	date_to = fields.Date(string='Fecha Fin', required=True)
	partner_ids = fields.Many2many(comodel_name='res.partner', relation='hierarchy_report_print_report_res_partner_rel', column1='hierarchy_report_print_id', column2='res_partner_id', string='Tercero')
	account_level = fields.Selection(ACCOUNT_LEVEL, string="Nivel Cuenta", default='1', help="Nivel de la cuenta que desea imprimir en el PDF o Excel")
	generation = fields.Selection(GENERATION, string=u"Opciones de Generación", help=u"Opciones de generación. Si elige Balance -> Imprimirá las cuentas 1,2 y 3. Si elige Estado -> Imprimirá las cuentas 4,5,6 y 7")
	show_lines = fields.Boolean(string="Mostrar Líneas")
	partner_id = fields.Many2one('res.partner', string="Tercero")

	filename = fields.Char('Nombre Archivo')
	document = fields.Binary(string = 'Descargar Excel')

	def return_information_company(self):
		"""
			Esta funcion permite retornar los datos mas importantes de la compania
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


	def execute_query_complete_data(self, date_from, date_to, partner_id):
		"""
			Funcion que permite retornar la data general
			gener la estructura princial, pero no contiene los valores totales del reporte
		"""
		if date_from and date_to:

			sql = """

				DROP TABLE IF EXISTS account_plan_relation;	
				SELECT
					account.code AS code,
					account.name AS account_name,
					0 AS initial_balance,
					(CASE WHEN (move_line.credit) IS NULL THEN 0 ELSE (move_line.credit) END) AS credit,
					(CASE WHEN (move_line.debit) IS NULL THEN 0 ELSE (move_line.debit) END) AS debit,
					(CASE WHEN (move_line.balance) IS NULL THEN 0 ELSE (move_line.balance) END) AS balance,
					move_line.date AS date,
					0 AS final_balance,
					move_line.partner_id,
					length(account.code) AS level

				INTO account_plan_relation 
				FROM account_move_line AS move_line,
						account_account AS account
			
				WHERE 	date BETWEEN '%(date_begin)s' AND '%(date_end)s' 
						AND move_line.account_id = account.id
						%(validation_partner)s

				ORDER BY account.code;
					

				INSERT INTO account_plan_relation (
					code,
					account_name,
					initial_balance,
					credit,
					debit,
					balance,
					final_balance,
					level
				)(SELECT code, name, 0, 0, 0, 0, 0 , length(code)
					FROM account_account WHERE code not in (SELECT code FROM account_plan_relation  GROUP BY code));


				SELECT 
					code,
					account_name,
					sum(initial_balance) AS initial_balance,
					sum(credit) AS credit,
					sum(debit) AS debit,
					sum(balance) AS balance,
					sum(final_balance) AS final_balance,
					level AS level
				FROM account_plan_relation
				GROUP BY code, account_name, level
				ORDER BY code;


			"""%{
			'date_begin': str(date_from),
			'date_end': str(date_to),
			'validation_partner': (' AND move_line.partner_id = ' + str(partner_id)) if partner_id else ' '
			}

			#print(sql)
			self.env.cr.execute(sql)
			res = self.env.cr.dictfetchall()

			return res


	def return_data_complete(self, date_from, date_to, partner_id):
		"""
			Funcion que permite retornar una data, la cual es el resultado de la sql general
		"""
		data_complete = self.execute_query_complete_data(date_from, date_to, partner_id)
		data = []
		if data_complete:
			for x in data_complete:
				vals = {
					'code': x['code'],
					'account_name': x['account_name'],
					'initial_balance': x['initial_balance'],
					'credit': x['credit'],
					'debit': x['debit'],
					'balance': x['balance'],
					'final_balance': x['final_balance'],
					'level': x['level']
				}
				data.append(vals)
		return data


	def execute_query_initial_balance(self, date_from, partner_id):
		"""
			Funcion que permite ejecutar una sql, la cual tiene una data con todas las cuentas y su respectivo saldo inicial
		"""
		if date_from:
			sql = """
				SELECT
				code,
				sum(move_line.balance) AS balance
				FROM account_account AS account
					LEFT JOIN account_move_line AS move_line
						ON (move_line.account_id=account.id)
					LEFT JOIN account_move as move
						ON (move_line.move_id=move.id)
				WHERE move_line.date < '%(date_from)s'
				%(validation_partner)s
				GROUP BY code
				ORDER BY code;

			"""%{
				'date_from': str(date_from),
				'validation_partner': (' AND move_line.partner_id = ' + str(partner_id)) if partner_id else ' '
			}

			#print(sql)
			self.env.cr.execute(sql)
			res = self.env.cr.dictfetchall()
			return res

	def return_data_initial_balance(self, date_from, partner_id):
		"""
			Funcion que permite retornar la data codigo de la cuenta y el respectivo balance
		"""
		data_balance = self.execute_query_initial_balance(date_from, partner_id)
		data = []
		if data_balance:
			for x in data_balance:
				vals = {
					'code': x.get('code'),
					'balance': x.get('balance'),
				}
				data.append(vals)
		return data


	def merge_data(self, date_from, date_to, partner_id):
		"""
			Funcion que permite realizar una mezcla entre la data principal y la data del saldo inicial
		"""
		data_complete = self.return_data_complete(date_from, date_to, partner_id)
		data_initial_balance = self.return_data_initial_balance(date_from, partner_id)
		data = []

		if data_initial_balance:
			for x in data_initial_balance:
				data_new = filter(lambda index: index['code'] == x['code'], data_complete)
				
				if data_new:
					for item in data_new:
						item['initial_balance'] = x['balance']
						item['final_balance'] = x['balance'] + item['debit'] - item['credit']
						data.append(item)
				else:
					data.append(x)

			for x in data_complete:
				data_new = (filter(lambda index: index['code'] == x['code'], data))
				if data_new:
					for item in data_new:
						x['initial_balance'] = item['initial_balance']

		for x in data_complete:
			x['final_balance'] = x['initial_balance'] + x['debit'] - x['credit']

		return data_complete


	def sum_parent_account_data(self, date_from, date_to, partner_id):
		"""
			Funcion que permite retornar la data completa, con la suma de cada uno de los niveles de cuenta
		"""
		data_main = self.merge_data(date_from, date_to, partner_id)
			
		if data_main:
			for x in data_main:
				data_new = list(filter(lambda index: index['code'].startswith(x['code']), data_main))
				if len(data_new) > 1:
					sum_initial_balance = 0
					sum_credit = 0
					sum_debit = 0
					sum_balance= 0
					sum_final_balance = 0
					for item in data_new:
						sum_initial_balance += item['initial_balance']
						sum_credit += item['credit']
						sum_debit += item['debit']
						sum_balance += item['balance']
						sum_final_balance += item['final_balance']

					x['initial_balance'] = sum_initial_balance
					x['credit'] = sum_credit
					x['debit'] = sum_debit
					x['balance'] = sum_balance
					x['final_balance'] = sum_final_balance
		return data_main


	def return_data_main(self, date_from, date_to, partner_id):
		"""
			Funcion que permite filtrar los registros que sean diferente de 0 en los cuatro campos
		"""
		data = self.sum_parent_account_data(date_from, date_to, partner_id)

		data_new = list(filter(lambda index: not ((index['initial_balance'] == 0) and (index['credit'] == 0) and (index['debit'] == 0) and (index['balance'] == 0) and (index['final_balance'] == 0)), data))
		return data_new

	def return_data_level(self, date_from, date_to, partner_id, account_level):
		"""
			Funcion que permite retornar los datos de acuerdo al nivel elegido por el usuario
		"""
		data = self.return_data_main(date_from, date_to, partner_id)
		data_new = list(filter(lambda index: (int(index['level']) <= int(account_level)), data))
		return data_new


	def options_generation(self, data, generation):
		"""
			Funcion que permite realizar un filtro 
			Opciones de generación. 
				Balance -> Imprimirá las cuentas 1,2 y 3 
				Estado -> Imprimirá las cuentas 4,5,6 y 7
		"""
		data_new = []
		if generation:
			if generation == 'balance':
				data_new = list(filter(lambda index: (index['code'].startswith('1') or index['code'].startswith('2') or index['code'].startswith('3')), data))

			if generation == 'state':
				data_new = list(filter(lambda index: (index['code'].startswith('4') or index['code'].startswith('5') or index['code'].startswith('6') or index['code'].startswith('7')), data))
		else:
			data_new = data

		return data_new

	@api.multi
	def generate_excel(self):
		"""
			Funcion que permite general el excel
		"""
		data_report = []
		data_main = self.return_data_level(self.date_from, self.date_to, self.partner_id.id, self.account_level)
		data_main = self.options_generation(data_main, self.generation)

		data_company = self.return_information_company()

		name_report = str('PLAN DE CUENTAS').upper()

		Header_Text = name_report
		file_data = BytesIO()
		workbook = xlsxwriter.Workbook(file_data)
		worksheet = workbook.add_worksheet(name_report)
		
		#Formato de letras y celdas
		bold = workbook.add_format({'bold': 1,'align':'left','border':1, 'font_size': 14})
		format_tittle = workbook.add_format({'bold': 1,'align':'center', 'valign':'vcenter', 'border':1, 'fg_color':'#F9CEA9', 'font_size': 25 })
		letter_gray_name = workbook.add_format({'align':'left', 'font_color': 'gray', 'indent':2, 'font_size': 14})
		letter_gray = workbook.add_format({'align':'right', 'font_color': 'gray', 'num_format': '$#,##0.00', 'font_size': 14})
		letter_black_name = workbook.add_format({'align':'right', 'font_color': 'black', 'num_format': '$#,##0.00', 'font_size': 14})
		letter_number = workbook.add_format({'align':'right', 'font_color': 'black', 'num_format': '$#,##0.00', 'font_size': 14})
		header_format = workbook.add_format({'bold': 1,'align':'center','valign':'vcenter', 'border':1, 'fg_color':'#F9CEA9', 'font_size': 18 })
		letter_black = workbook.add_format({'align':'left', 'font_color': 'black', 'num_format': '$#', 'font_size': 14})
		letter_black_number = workbook.add_format({'bold': 1, 'align':'right', 'font_color': 'black', 'num_format': '$#,##0.00', 'font_size': 16, 'border':1, 'fg_color':'#F9CEA9'})

		worksheet.set_column('A1:A1',25)
		worksheet.set_column('B1:B1',45)
		worksheet.set_column('C1:C1',25)
		worksheet.set_column('D1:D1',25)
		worksheet.set_column('E1:E1',25)
		worksheet.set_column('F1:F1',25)
		worksheet.set_column('G1:G1',25)
		worksheet.set_column('H1:H1',40)
		worksheet.set_column('J1:J1',40)
		worksheet.set_column('K1:K1',40)
		worksheet.set_column('L1:L1',40)

		preview = name_report 

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

			worksheet.merge_range('C3:D4',preview, format_tittle)

			if self.partner_id:
				worksheet.write('A9', "TERCERO", header_format)
				worksheet.write('A10', str(self.partner_id.name), bold)

			worksheet.merge_range('F7:G7', "Rango de Fechas", header_format)
			worksheet.write('F8', "Fecha Inicial", bold)
			worksheet.write('G8', str(self.date_from), bold)
			worksheet.write('F9', "Fecha Final", bold)
			worksheet.write('G9', str(self.date_to), bold)

			format="%Y-%m-%d %H:%M:00"
			now=fields.Datetime.context_timestamp(self, fields.Datetime.from_string(fields.Datetime.now()))
			date_today=str(datetime.strftime(now, format))
			date_create= str("Fecha Creacion")
			worksheet.write('G1', date_create, header_format)
			worksheet.write('G2', date_today, bold)

			if len(data_main) > 0:

				worksheet.write('A13', 'CODIGO', header_format)
				worksheet.write('B13', 'CUENTA', header_format)
				worksheet.write('C13', 'SALDO INICIAL', header_format)
				worksheet.write('D13', 'DEBITOS', header_format)
				worksheet.write('E13', 'CREDITOS', header_format)
				worksheet.write('F13', 'SALDO PERIODO', header_format)
				worksheet.write('G13', 'SALDO FINAL', header_format)

				row=13
				col=0

				sum_initial_balance = 0
				sum_credit = 0
				sum_debit = 0
				sum_balance = 0
				sum_final_balance = 0

				for x in data_main:
					#worksheet.merge_range(row,col, row ,col +1, x['account'] or '', letter_black)
					#print(str(x['account']).split(' ', 1))
					worksheet.write(row,col , str(x['code']) or '', letter_black)
					worksheet.write(row,col+1 , str(x['account_name']) or '', letter_black)
					worksheet.write(row,col+2 , x['initial_balance'] or 0, letter_number)
					worksheet.write(row,col+3 , x['debit'] or 0, letter_number)
					worksheet.write(row,col+4 , x['credit'] or 0, letter_number)
					worksheet.write(row,col+5 , x['balance'] or 0, letter_number)
					worksheet.write(row,col+6 , x['final_balance'] or 0, letter_number)

					sum_initial_balance += x['initial_balance']
					sum_credit += x['credit']
					sum_debit += x['debit']
					sum_balance += x['balance']
					sum_final_balance += x['final_balance']

					row+=1

				worksheet.write(row,col , '', letter_black_number)
				worksheet.write(row,col+1 , 'TOTAL', letter_black_number)
				worksheet.write(row,col+2 , sum_initial_balance, letter_black_number)
				worksheet.write(row,col+3 , sum_debit or 0, letter_black_number)
				worksheet.write(row,col+4 , sum_credit or 0, letter_black_number)
				worksheet.write(row,col+5 , sum_balance or 0, letter_black_number)
				worksheet.write(row,col+6 , sum_final_balance, letter_black_number)

			workbook.close()
			file_data.seek(0)

		self.write({'document':base64.encodestring(file_data.read()), 'filename':Header_Text+'.xlsx'})
			
		return {
			'name': _(u'Reporte de Plan de Cuentas'),
			'res_model':'hierarchy.report_print',
			'type':'ir.actions.act_window',
			'view_type':'form',
			'view_mode':'form',
			'target':'new',
			'nodestroy': True,
			'res_id': self.id
		}


	def _build_contexts(self, data):
		"""
			Funcion que permite construir un contexto con los filtros que se realizaron, como tambien agregando una data para el reporte
		"""
		result = {}
		result['date_from'] =  self.date_from
		result['date_to'] =  self.date_to
		result['account_level'] =  self.account_level
		result['generation'] =  self.generation
		result['partner_id'] = self.partner_id.id

		return result

	def _print_report(self, data):
		"""
			Funcion que permite retornar el template del reporte
		"""
		return self.env.ref('l10n_co_account_hierarchy_report.action_report_hierarchy_report_print').with_context(landscape=True).report_action(self, data=data)

	@api.multi
	def generate_pdf(self):
		"""
			Funcion que permite generar el reporte pdf del plan contable
		"""
		self.ensure_one()

		data = {}
		data['ids'] = self.env.context.get('active_ids', [])
		data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
		data['form'] = self.read(['date_from', 'date_to','user_ids', 'journal_ids'])[0]
		used_context = self._build_contexts(data)

		data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang'))

		return self.with_context(discard_logo_check=True)._print_report(data)


HierarchyReportPrint()
