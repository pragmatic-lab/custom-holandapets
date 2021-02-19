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

import re
from datetime import datetime, timedelta, date

import xlsxwriter
from io import BytesIO
import base64

from odoo import api, fields, models, _

from odoo.exceptions import UserError
from odoo.tools import pycompat
from odoo.tools.translate import _
from odoo.tools.misc import formatLang, format_date, get_user_companies

import sys
import requests

class ReportCertificationsBase(models.TransientModel):
	_name = 'report.certification_base'
	_description = "Colombian Certification Report"

	date_begin = fields.Date(string='Fecha Inicio', required=True, default=fields.Date.context_today)
	date_end = fields.Date(string='Fecha Fin',  required=True, default=fields.Date.context_today)
	
	
	filename = fields.Char('Nombre Archivo')
	document = fields.Binary(string = 'Descargar Excel')

	#TO BE OVERWRITTEN
	def _get_report_name(self):
		return _('General Report')

	def _get_bimonth_for_aml(self, aml):
		"""
			Funcion que permite retornar el numero del mes, cada dos meses.
		"""
		# month:   1   2   3   4   5   6   7   8   9   10  11   12
		# bimonth: \ 1 /   \ 2 /   \ 3 /   \ 4 /   \ 5 /    \ 6 /
		bimonth = aml.date.month
		bimonth = (bimonth + 1) // 2
		return bimonth

	def _get_bimonth_name(self, bimonth_index):
		"""
			Funcion que permite retornar el nombre del bimes
		"""
		bimonth_names = {
			1: 'Enero - Febrero',
			2: 'Marzo - Abril',
			3: 'Mayo - Junio',
			4: 'Julio - Agosto',
			5: 'Septiembre - Octubre',
			6: 'Noviembre - Diciembre',
		}
		return bimonth_names[bimonth_index]

	def format_value(self, value, currency=False):
		currency_id = currency or self.env.user.company_id.currency_id
		if self.env.context.get('no_format'):
			return currency_id.round(value)
		if currency_id.is_zero(value):
			# don't print -0.0 in reports
			value = abs(value)
		res = formatLang(self.env, value, currency_obj=currency_id)
		return res
		
	def _get_domain(self):
		"""
			Permite retornar el dominio principal
		"""
		common_domain = [('partner_id', '!=', False)]

		if self.date_begin and self.date_end:
			common_domain += [('date', '>=', self.date_begin),
							  ('date', '<=', self.date_end)]
		return common_domain

	def _handle_aml(self, aml, lines_per_bimonth):
		raise NotImplementedError()

	def _get_values_for_columns(self, values):
		raise NotImplementedError()

	def _add_to_partner_total(self, totals, new_values):
		for column, value in new_values.items():
			if isinstance(value, pycompat.string_types):
				totals[column] = ''
			else:
				totals[column] = totals.get(column, 0) + value

	def _generate_lines_for_partner(self, partner_id, lines_per_group):
		lines = []
		if lines_per_group:

			identication = ''
			if partner_id.is_company:
				identication = partner_id.formatedNit
			else:
				identication = partner_id.xidentification

			phone = ''
			if partner_id.mobile:
				phone = partner_id.mobile + ' '
			if partner_id.phone:
				phone += partner_id.phone

			street = ''
			if partner_id.street:
				street = partner_id.street + ' '
			if partner_id.xcity:
				street += partner_id.xcity.name + ' '
			if partner_id.state_id:
				street += partner_id.state_id.name


			partner_line = {
				'id': 'partner_%s' % (partner_id.id),
				'partner_id': partner_id.id,
				'partner_vat': identication,
				'partner_phone': phone,
				'partner_street': street,
				'name': partner_id.name.upper(),
				'level': 2,
				'unfoldable': True,
				'unfolded': 'partner_%s' % (partner_id.id),
			}
			lines.append(partner_line)

			partner_totals = {}
			for group, values in lines_per_group.items():
				self._add_to_partner_total(partner_totals, values)
				if 'partner_%s' % (partner_id.id):
					lines.append({
						'id': 'line_%s_%s' % (partner_id.id, group),
						'name': '',
						'unfoldable': False,
						'columns': self._get_values_for_columns(values),
						'level': 1,
						'parent_id': 'partner_%s' % (partner_id.id),
						'partner_id': partner_id.id
					})
			partner_line['columns'] = self._get_values_for_columns(partner_totals)

		return lines

	def _get_lines(self, line_id=None):
		lines = []
		domain = []

		domain += self._get_domain()

		if line_id:
			partner_id = re.search('partner_(.+)', line_id).group(1)
			if partner_id:
				domain += [('partner_id.id', '=', partner_id)]

		amls = self.env['account.move.line'].search(domain, order='partner_id, id')

		previous_partner_id = self.env['res.partner']
		lines_per_group = {}

		for aml in amls:
			if previous_partner_id != aml.partner_id:
				partner_lines = self._generate_lines_for_partner(previous_partner_id, lines_per_group)
				if partner_lines:
					lines += partner_lines
					lines_per_group = {}
				previous_partner_id = aml.partner_id

			self._handle_aml(aml, lines_per_group)


		lines += self._generate_lines_for_partner(previous_partner_id, lines_per_group)

		return lines



	def return_information_company(self):
		"""
			Funcion que permite retornar los datos mas importantes de la compania para el reporte de excel
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

	def return_excel(self):
		"""
			Funcion que permite retornar la vista para descargar el excel
		"""
		return {}


	def generate_header_excel(self, worksheet, bold, header_format, format_tittle):
		"""
			Funcion que permite generar el encabezado del informe de excel
		"""
		data_company = self.return_information_company()

		worksheet.set_column('A1:A1',55)
		worksheet.set_column('B1:B1',45)
		worksheet.set_column('C1:C1',45)
		worksheet.set_column('D1:D1',45)
		worksheet.set_column('E1:E1',45)
		worksheet.set_column('F1:F1',25)
		worksheet.set_column('G1:G1',35)
		worksheet.set_column('H1:H1',20)
		worksheet.set_column('I1:I1',20)

		preview = self._get_report_name()

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

			worksheet.merge_range('F7:G7', "Rango de Fechas", header_format)
			worksheet.write('F8', "Fecha Inicial", bold)
			worksheet.write('G8', str(self.date_begin), bold)
			worksheet.write('F9', "Fecha Final", bold)
			worksheet.write('G9', str(self.date_end), bold)

			format="%Y-%m-%d %H:%M:00"
			now=fields.Datetime.context_timestamp(self, fields.Datetime.from_string(fields.Datetime.now()))
			date_today=str(datetime.strftime(now, format))
			date_create= str("Fecha Creacion")
			worksheet.write('G1', date_create, header_format)
			worksheet.write('G2', date_today, bold)


	def return_columns_excel(self, worksheet, header_format):
		"""
			Permite retornar las columnas para el reporte de excel
		"""
		columns = self._get_columns_name()

		row = 13
		col = 0

		if columns:
			for x in columns:
				worksheet.write(row,col, x['name'], header_format)
				col+= 1


	def generate_body_excel(self, worksheet, header_format, letter_black_name, bold_total, lines):
		"""
			Funcion que se encarga de armar el body completo del excel
		"""

		self.return_columns_excel(worksheet, header_format)

		row=14

		for x in lines:
			col=0

			if x['unfoldable']:
				worksheet.write(row,col , str(x['name']) or '', letter_black_name)
				col+= 1
				if x['columns']:
					for column in x['columns']:
						worksheet.write(row,col , str(column['name']), letter_black_name)
						col+= 1
				row+=1

	def generate_data_complete_excel(self, worksheet, bold, header_format, format_tittle, letter_black_name, bold_total, lines):
		"""
			Permite generar el excel completo
			header
			body
		"""
		self.generate_header_excel(worksheet, bold, header_format, format_tittle)
		self.generate_body_excel(worksheet, header_format, letter_black_name, bold_total, lines)


	@api.multi
	def generate_excel(self):
		"""
		Funcion que permite generar el excel
		"""

		lines = self._get_lines()

		format="%Y-%m-%d %H:%M:00"
		now=fields.Datetime.context_timestamp(self, fields.Datetime.from_string(fields.Datetime.now()))
		date_today=str(datetime.strftime(now, format))

		
		name_report = self._get_report_name()

		Header_Text = name_report
		file_data = BytesIO()
		workbook = xlsxwriter.Workbook(file_data)

		worksheet = workbook.add_worksheet('Hoja 1')

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
		
		self.generate_data_complete_excel(worksheet, bold, header_format, format_tittle, letter_black_name, bold_total, lines)

		workbook.close()
		file_data.seek(0)

		date_from_ = self.date_begin
		date_to_ = self.date_end
		self.write({'document':base64.encodestring(file_data.read()), 'filename':Header_Text + '  ' + str(date_from_) + ' - ' + str(date_to_) +'.xlsx'})


		return self.return_excel()


	"""
		Funciones para generar el excel
	"""
	def _build_contexts(self, data):
		"""
			Funcion que permite construir un contexto con los filtros que se realizaron, como tambien agregando una data para el reporte
		"""
		result = {}
		result['date_begin'] = (self.date_begin)
		result['date_end'] = self.date_end
		result['name_report'] = self._get_report_name()
		result['columns'] = self._get_columns_name()
		result['lines'] = self._get_lines()
		result['data_company'] = self.return_information_company()
		result['begin_month'] = self.return_date_month(self.date_begin)
		result['end_month'] = self.return_date_month(self.date_end)
		return result


	def translate_world(self, source, target, text):
		parametros = {'sl': source, 'tl': target, 'q': text}
		cabeceras = {"Charset":"UTF-8","User-Agent":"AndroidTranslate/5.3.0.RC02.130475354-53000263 5.1 phone TRANSLATE_OPM5_TEST_1"}
		url = "https://translate.google.com/translate_a/single?client=at&dt=t&dt=ld&dt=qca&dt=rm&dt=bd&dj=1&hl=es-ES&ie=UTF-8&oe=UTF-8&inputm=2&otf=2&iid=1dd3b944-fa62-4b55-b330-74909a99969e"
		response = requests.post(url, data=parametros, headers=cabeceras)
		print(response.status_code)
		if response.status_code == 200:
			for x in response.json()['sentences']:
				return x['trans']
		else:
			return "Ocurrió un error"

	def return_date_month(self, date):
		return_date = date
		return_date = return_date.strftime('%B %d %Y')

		return_date = self.translate_world("en", "es", str(return_date))

		return return_date

	def _print_report(self, data):
		"""
			Funcion que permite retornar el template del reporte
		"""
		return self.env.ref('l10n_co_reports.action_report_certification_base_document').with_context(landscape=True).report_action(self, data=data)

	@api.multi
	def generate_pdf(self):
		"""
			Funcion que permite generar el reporte pdf general del dia
		"""
		self.ensure_one()

		data = {}
		data['ids'] = self.env.context.get('active_ids', [])
		data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
		data['form'] = self.read(['date_begin', 'date_end'])[0]
		used_context = self._build_contexts(data)

		data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang'))

		return self.with_context(discard_logo_check=True)._print_report(data)




		
ReportCertificationsBase()