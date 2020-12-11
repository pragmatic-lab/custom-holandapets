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
					('8', 'Nivel 8')]

	date_from = fields.Date(string='Fecha Inicio', required=True)
	date_to = fields.Date(string='Fecha Fin', required=True)
	partner_ids = fields.Many2many(comodel_name='res.partner', relation='hierarchy_report_print_report_res_partner_rel', column1='hierarchy_report_print_id', column2='res_partner_id', string='Tercero')
	account_level = fields.Selection(ACCOUNT_LEVEL, string="Nivel Cuenta", default='1', help="Nivel de la cuenta que desea imprimir en el PDF o Excel")
	show_lines = fields.Boolean(string="Mostrar Líneas")
	partner_id = fields.Many2one('res.partner', string="Tercero")

	filename = fields.Char('Nombre Archivo')
	document = fields.Binary(string = 'Descargar Excel')


	def return_value_sum(self, value):
		query = """
				(SELECT
			 		sum(%(name)s)
				FROM account_plan_relation 
				WHERE code LIKE (val || %(percent)s)
				AND date BETWEEN '%(date_from)s' AND '%(date_to)s');
		"""


		if self.partner_id:
			query = """
					(SELECT
				 		sum(%(name)s)
					FROM account_plan_relation 
					WHERE code LIKE (val || %(percent)s)
					AND date BETWEEN '%(date_from)s' AND '%(date_to)s'
					AND partner_id = %(partner_id)s);
			"""



		return query%{
		'name': value,
		'percent': "'%'",
		'date_from': str(self.date_from),
		'date_to': str(self.date_to),
		'partner_id': self.partner_id.id if self.partner_id else ''
		}


	def return_fill_account_plan(self, value):

		"""
			Funcion que permite reotornar una funcion para la sql con el valor del credito de la cuentaque ingrese por parametro
		"""

		result = """
		CREATE OR REPLACE FUNCTION fill_account_plan_%s(val varchar) RETURNS numeric AS $$
			BEGIN

			RETURN %s
									 
			END; $$
			LANGUAGE PLPGSQL;	

		"""

		if self.partner_id:


			result = """
			CREATE OR REPLACE FUNCTION fill_account_plan_%s(val varchar, val_partner integer) RETURNS numeric AS $$
				BEGIN

				RETURN %s
										 
				END; $$
				LANGUAGE PLPGSQL;	

			"""

		return result%(value, self.return_value_sum(value))

	def return_execute_query(self):

		"""
			Funcion que permite armar la sql general para poder sacar los valores acumulables de la cuentas
		"""

		query_select = """

			DROP TABLE IF EXISTS account_plan_relation;
			SELECT
				length(account.code) AS level_account,
				account.code AS code,
				concat_ws(' ',account.code::text, account.name::text) AS name,
				(CASE WHEN sum(move_line.credit) IS NULL THEN 0 ELSE sum(move_line.credit) END) AS credit,
				(CASE WHEN sum(move_line.debit) IS NULL THEN 0 ELSE sum(move_line.debit) END) AS debit,
				(CASE WHEN sum(move_line.balance) IS NULL THEN 0 ELSE sum(move_line.balance) END) AS balance,
				sum(0) AS sum_credit,
				sum(0) AS sum_debit,
				sum(0) AS sum_balance,
				move_line.date AS date

		"""


		query_into = " INTO account_plan_relation "

		query_from = """

			FROM account_account AS account
				LEFT JOIN account_move_line AS move_line
					ON (move_line.account_id=account.id)
				LEFT JOIN account_move as move
					ON (move_line.move_id=move.id)


		"""

		query_where =" WHERE move_line.date BETWEEN '" + str(self.date_from) + "' AND '" + str(self.date_to) + "'  AND move_line.date is not null OR move_line.date is null   "
			
			
		query_group_by = """

			GROUP BY 
				account.code,
				account.name,
				move_line.date
		"""

		query_order_by = " ORDER BY account.code;  "

		if self.partner_id:

			query_select += ", partner.name AS name_partner, move_line.partner_id "
			query_from += """
							LEFT JOIN res_partner partner
								ON (move_line.partner_id = partner.id)
						"""
			query_where += " AND move_line.partner_id = " + str(self.partner_id.id) + "  AND move_line.partner_id is not null OR move_line.partner_id is null "
			query_group_by += " , partner.name, move_line.partner_id"


		query = query_select + query_into + query_from + query_where + query_group_by + query_order_by
		
		query += self.return_fill_account_plan('credit')
		query += self.return_fill_account_plan('debit')
		query += self.return_fill_account_plan('balance')

		consult_select = """
			DROP TABLE IF EXISTS account_plan_relation_data;
			SELECT 
				level_account,
				code,
				name,
		"""

		if self.partner_id:
			consult_select += """
				(CASE WHEN fill_account_plan_credit(code, partner_id) IS NULL THEN 0 ELSE fill_account_plan_credit(code, partner_id) END) AS sum_credit,
				(CASE WHEN fill_account_plan_debit(code, partner_id) IS NULL THEN 0 ELSE fill_account_plan_debit(code, partner_id) END) AS sum_debit,
				(CASE WHEN fill_account_plan_balance(code, partner_id) IS NULL THEN 0 ELSE fill_account_plan_balance(code, partner_id) END) AS sum_balance
			"""
		else:
			consult_select += """
				(CASE WHEN fill_account_plan_credit(code) IS NULL THEN 0 ELSE fill_account_plan_credit(code) END) AS sum_credit,
				(CASE WHEN fill_account_plan_debit(code) IS NULL THEN 0 ELSE fill_account_plan_debit(code) END) AS sum_debit,
				(CASE WHEN fill_account_plan_balance(code) IS NULL THEN 0 ELSE fill_account_plan_balance(code) END) AS sum_balance
			"""

		consult_from = """ 
					INTO account_plan_relation_data  
					FROM account_plan_relation 
					WHERE level_account <= %(level)s ;
					"""%{
					'level': self.account_level
					}

		query += consult_select + consult_from


		query_final = """

			SELECT 
			code,
			name,
			sum(sum_credit) AS total_credit,
			sum(sum_debit) AS total_debit,
			sum(sum_balance) AS total_balance
			FROM account_plan_relation_data
			WHERE sum_credit <> 0
			AND sum_debit <> 0
			AND sum_balance <> 0
			GROUP BY code, name
			ORDER BY code;

		"""

		query += query_final

						
		return query

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


	@api.multi
	def generate_excel(self):

		data_report = self.return_execute_query()
		print(data_report)
		data_company = self.return_information_company()


		name_report = str(data_report['name_report']).upper()

		Header_Text = name_report
		file_data = StringIO()
		workbook = xlsxwriter.Workbook(file_data)
		worksheet = workbook.add_worksheet(name_report)
		
		#Formato de letras y celdas
		bold = workbook.add_format({'bold': 1,'align':'left','border':1, 'font_size': 14})
		format_tittle = workbook.add_format({'bold': 1,'align':'center', 'valign':'vcenter', 'border':1, 'fg_color':'#F9CEA9', 'font_size': 25 })
		letter_gray_name = workbook.add_format({'align':'left', 'font_color': 'gray', 'indent':2, 'font_size': 14})
		letter_gray = workbook.add_format({'align':'right', 'font_color': 'gray', 'num_format': '$#,##0.00', 'font_size': 14})
		letter_black_name = workbook.add_format({'align':'left', 'font_color': 'black', 'num_format': '$#,##0.00', 'font_size': 14})
		letter_black = workbook.add_format({'align':'right', 'font_color': 'black', 'num_format': '$#,##0.00', 'font_size': 14})
		header_format = workbook.add_format({'bold': 1,'align':'center','valign':'vcenter', 'border':1, 'fg_color':'#F9CEA9', 'font_size': 18 })


		worksheet.set_column('A1:A1',35)
		worksheet.set_column('B1:B1',35)
		worksheet.set_column('C1:C1',35)
		worksheet.set_column('D1:C1',35)
		worksheet.set_column('E1:E1',35)
		worksheet.set_column('F1:F1',35)
		worksheet.set_column('G1:G1',35)
		worksheet.set_column('H1:H1',35)
		worksheet.set_column('J1:J1',35)
		worksheet.set_column('K1:K1',35)
		worksheet.set_column('L1:L1',35)

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

			if data_report['target_move']:
				worksheet.write('A9', "Movimientos Senalados", header_format)
				worksheet.write('A10', data_report['target_move'], bold)


			if data_report['display_account']:
				worksheet.write('C9', "Cuentas", header_format)
				worksheet.write('C10', data_report['display_account'], bold)

			if data_report['validate_date']:
				worksheet.merge_range('E9:F9', "Rango de Fechas", header_format)
				worksheet.write('E10', "Fecha Inicial", bold)
				worksheet.write('F10', data_report['date_to'], bold)
				worksheet.write('E11', "Fecha Final", bold)
				worksheet.write('F11', data_report['date_from'], bold)

			format="%Y-%m-%d %H:%M:00"
			now=fields.Datetime.context_timestamp(self, fields.Datetime.from_string(fields.Datetime.now()))
			date_today=str(datetime.strftime(now, format))
			date_create= unicode(str("Fecha Creación").encode("utf8"))
			date_create= date_create.encode('utf-8')
			worksheet.write('F1', date_create, header_format)
			worksheet.write('F2', date_today, bold)

			if len(data_report['data_account']) > 0:

				worksheet.merge_range('A13:C13', "Nombre", header_format)

				if data_report['debit_credit']:
					worksheet.write('D13', 'Debito', header_format)
					worksheet.write('E13', 'Credito', header_format)
					worksheet.write('F13', 'Saldo Pendiente', header_format)
				else:
					worksheet.write('D13', 'Saldo Pendiente', header_format)

				row=13
				col=0

				for x in data_report['data_account']:
					cadena= unicode(x['name'].encode("utf8"))
					cadena= cadena.encode('utf-8')

					format_letter= letter_black

					if x['with_partner']:
						format_letter = letter_gray 
						worksheet.write(row,col, cadena or '', letter_gray_name)

					else:

						format_letter = letter_black
						worksheet.write(row,col, cadena or '', letter_black_name)

					if data_report['debit_credit']:

						worksheet.write(row,col+3 , x['debit'] or 0, format_letter)
						worksheet.write(row,col+4 , x['credit'] or 0, format_letter)
						worksheet.write(row,col+5 , x['balance'] or 0, format_letter)
			
					else:

						worksheet.write(row,col+3 , x['balance'] or 0, format_letter)
					
					row+=1


			workbook.close()
			file_data.seek(0)

		self_id= 0
		for x in docargs['docs']:
			_logger.info('holis')
			_logger.info(x.id)
			self_id= x.id
			x.write({'document':base64.encodestring(file_data.read()), 'filename':Header_Text+'.xlsx'})
			
		return {
			'name': _(u'Valuación del Inventario'),
			'res_model':'stock.quantity.history',
			'type':'ir.actions.act_window',
			'view_type':'form',
			'view_mode':'form',
			'target':'new',
			'nodestroy': True,
			'res_id': self.id
		}


HierarchyReportPrint()