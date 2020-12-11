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

class CommissionVendor(models.Model):
	_name = "commission.vendor"

	date_from = fields.Date(string='Fecha Inicio', default=fields.Date.context_today, required=True)
	date_to = fields.Date(string='Fecha Fin', default=fields.Date.context_today, required=True)
	type_commission = fields.Many2one('commission.vendor.conf.master', string=u"Tipo Comisión", required=True)
	commission_vendor_conf_ids = fields.One2many('commission.vendor.conf', 'commision_vendor_id', string="Comisiones")
	user_ids = fields.Many2many('res.users', 'report_commission_vendor_user', column1='commission_vendor_id', column2="user_id", string="Tercero")
	filename = fields.Char('Nombre Archivo')
	document = fields.Binary(string = 'Descargar Excel')

	@api.onchange('type_commission')
	def onchange_type_commission(self):
		"""
			Funcion que permite cargar automaticamente los rangos de la comision que se configuraron previamente
			en el tipo de comision
		"""
		if self.type_commission:
			if self.type_commission.commission_vendor_conf_ids:
				self.commission_vendor_conf_ids = self.type_commission.commission_vendor_conf_ids
			else:
				self.commission_vendor_conf_ids = None
		else:
			self.commission_vendor_conf_ids = None

	def return_data_invoice(self, date_begin, date_end, user_id):
		"""
			Permite retornar las facturas que se encuentran en esa fecha, como tambien filtrarlos por los vendedores
		"""
		invoice_ids = None
		if date_begin and date_end:
			if user_id:
				invoice_ids = self.env['account.invoice'].search([('date_invoice', '>=', date_begin), ('date_invoice', '<=', date_end), ('user_id', '=', user_id), ('state', 'in', ['open', 'in_payment', 'paid']), ('type', '=', 'out_invoice')])
				
		return invoice_ids

	def validate_record_payments(self, data):
		for x in data:
			if x.payment_ids:
				return True
		return False

					

	def return_days(self, date_invoice, date_due):
		"""
			Funcion que permite retornar el numero de dias que hay entre la fecha de la factura y la fecha de vencimiento de la factura
		"""
		date_invoice = datetime.strptime(date_invoice, "%Y-%m-%d")
		date_due = datetime.strptime(date_due, "%Y-%m-%d")

		return abs((date_due - date_invoice).days)

	def return_data_commission(self, commission_vendor_conf_ids):
		"""
			Funcion que permite retornar la configuracion seleccionada por el usuario en el wizard
		"""
		
		data = []
		if self.commission_vendor_conf_ids:
			for x in self.commission_vendor_conf_ids:
				vals = {
					'day_begin': str(x.day_begin),
					'day_end': str(x.day_end),
					'value_commission': x.value_commission
				}
				data.append(vals)
		return data

	def return_commission_item(self, days, data_commission):
		"""
			Funcion que permite retornar el item de la commission en el cual se encuentra el numero de dias
		"""
		if data_commission:
			for x in data_commission:
				if (x['day_begin'] != 'hundred_more') or (x['day_end'] != 'hundred_more'):
					if (days >= int(x['day_begin'])) and (days <= int(x['day_end'])):
						return x					
				if (x['day_begin'] != 'hundred_more') and (x['day_end'] == 'hundred_more'):
					if (days >= int(x['day_begin'])) and (days <= 500):
						return x

	def return_comission(self, date_invoice, date_due, commission_vendor_conf_ids):
		"""
			Funcion que permite retornar la comision a la que pertenece segun los dias
		"""
		commission = []
		if date_invoice and date_due:
			days = self.return_days(date_invoice, date_due)
			data_commission = commission_vendor_conf_ids 
			commission = self.return_commission_item(days, data_commission)

		return commission


	def return_excel(self):
		"""
			Funcion que permite retornar la vista para descargar el excel
		"""
		return {
			'name': _(u'Comisión de Vendedor'),
			'res_model':'commission.vendor',
			'type':'ir.actions.act_window',
			'view_type':'form',
			'view_mode':'form',
			'target':'new',
			'nodestroy': True,
			'res_id': self.id
		}

	def return_state(self, state):
		"""
			Funcion que permite retornar el nombre del estado
		"""
		name_state = ''
		if state:
			if state == 'paid':
				name_state = 'Pagado'
			if state == 'in_payment':
				name_state = 'En proceso de Pago'
			if state == 'open':
				name_state = 'Abierto'
		return name_state

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


	def generate_body_excel(self, data, worksheet, user_id, model_spai, header_format, letter_black, bold_total, letter_black_name, bold_total_color, bold_total_gray, format_diag, header_format_subtitle):
		
		if data:
			worksheet.write('A13', 'FECHA', header_format)
			worksheet.write('B13', 'FECHA VENCIMIENTO', header_format)
			worksheet.write('C13', 'NUMERO DIAS', header_format)
			worksheet.write('D13', 'FACTURA', header_format)
			worksheet.write('E13', 'CLIENTE', header_format)
			worksheet.write('F13', 'ORIGEN', header_format)
			worksheet.write('G13', 'ASIENTO CONTABLE', header_format)
			worksheet.write('H13', 'ESTADO', header_format)
			worksheet.write('I13', 'RANGO DIAS', header_format)
			worksheet.write('J13', 'COMISION (%)', header_format)
			worksheet.write('K13', 'REF. PAGO', header_format)
			worksheet.write('L13', 'CIRCULAR', header_format)
			worksheet.write('M13', 'MONTO PAGO', header_format)
			worksheet.write('N13', 'TOTAL SIN IVA', header_format)
			worksheet.write('O13', 'TOTAL', header_format)
			worksheet.write('P13', 'TOTAL PAGADO', header_format)
			worksheet.write('Q13', 'TOTAL ADEUDADO', header_format)
			worksheet.write('R13', 'BASE COMISION', header_format)
			worksheet.write('S13', 'COMISION', header_format)

			row=13
			col=0

			sum_amount_total = 0
			sum_payment = 0
			sum_residual = 0
			sum_commission = 0
			sum_untaxed = 0
			sum_payment_user = 0
			sum_base_total_commission = 0

			for x in data:

				if x.payment_ids:

					for payment in x.payment_ids:

						data_commission = self.return_comission(str(x.date_invoice), str(x.date_due), self.return_data_commission(self.commission_vendor_conf_ids))
						
						range_days = data_commission['day_begin'] + '  - ' + data_commission['day_end'] + ' dias'
						percent_commission = data_commission['value_commission']

						#total_commission = (percent_commission/100) * x.amount_untaxed
						base_total_commission = (payment.amount*x.amount_untaxed)/x.amount_total
						total_commission = (percent_commission/100) * base_total_commission

						worksheet.write(row,col , str(x.date_invoice) or '', letter_black_name)
						worksheet.write(row,col+1 , str(x.date_due) or '', letter_black_name)
						worksheet.write(row,col+2 , self.return_days(str(x.date_invoice), str(x.date_due)) or 0, letter_black_name)
						worksheet.write(row,col+3 , x.number or '', letter_black_name)
						worksheet.write(row,col+4 , x.partner_id.name or '', letter_black_name)
						worksheet.write(row,col+5 , x.origin or '', letter_black_name)
						worksheet.write(row,col+6 , x.move_id.name or '', letter_black_name)
						worksheet.write(row,col+7 , self.return_state(x.state), letter_black_name)
						worksheet.write(row,col+8 , range_days, letter_black_name)
						worksheet.write(row,col+9 , percent_commission, letter_black_name)
						worksheet.write(row,col+10 , payment.name, letter_black_name)
						worksheet.write(row,col+11 , payment.communication, letter_black_name)
						worksheet.write(row,col+12 , payment.amount or 0, bold_total)
						worksheet.write(row,col+13 , x.amount_untaxed or 0, bold_total)
						worksheet.write(row,col+14 , x.amount_total or 0, bold_total)
						worksheet.write(row,col+15 , (x.amount_total - x.residual) or 0, bold_total)
						worksheet.write(row,col+16 , x.residual or 0, bold_total)
						worksheet.write(row,col+17 , base_total_commission or 0, bold_total)
						worksheet.write(row,col+18 , total_commission or 0, bold_total_gray)

						sum_amount_total += x.amount_total
						sum_payment += (x.amount_total - x.residual)
						sum_residual += x.residual
						sum_commission += total_commission
						sum_untaxed += x.amount_untaxed
						sum_payment_user += payment.amount
						sum_base_total_commission += base_total_commission
						row+=1

			worksheet.write(row,col , '', letter_black_name)
			worksheet.write(row,col+1 , '', letter_black_name)
			worksheet.write(row,col+2 , '', letter_black_name)
			worksheet.write(row,col+3 , '', letter_black_name)
			worksheet.write(row,col+4 , '', letter_black_name)
			worksheet.write(row,col+5 , '', letter_black_name)
			worksheet.write(row,col+6 , '', letter_black_name)
			worksheet.write(row,col+7 , '', letter_black_name)
			worksheet.write(row,col+8 , '', letter_black_name)
			worksheet.write(row,col+9 , '', letter_black_name)
			worksheet.write(row,col+10 , '', letter_black_name)
			worksheet.write(row,col+11, 'TOTAL', header_format)
			worksheet.write(row,col+12 , sum_payment_user, bold_total_color)
			worksheet.write(row,col+13 , sum_untaxed, bold_total_color)
			worksheet.write(row,col+14 , sum_amount_total, bold_total_color)
			worksheet.write(row,col+15 , sum_payment or 0, bold_total_color)
			worksheet.write(row,col+16 , sum_residual or 0, bold_total_color)
			worksheet.write(row,col+17 , sum_base_total_commission or 0, bold_total_color)
			worksheet.write(row,col+18 , sum_commission or 0, bold_total_color)
			row+=1



	def generate_data_complete_excel(self, data, worksheet, user_id, user_name, model_invoice, bold, header_format, format_tittle, letter_black, bold_total, letter_black_name, bold_total_color, bold_total_gray, format_diag, header_format_subtitle):
		"""
			Permite generar el excel completo
			header
			body
		"""
		self.generate_header_excel(worksheet, user_name, user_id, bold,  header_format, format_tittle)
		self.generate_body_excel(data, worksheet, user_id, model_invoice, header_format, letter_black, bold_total, letter_black_name, bold_total_color, bold_total_gray, format_diag, header_format_subtitle)


	def generate_header_excel(self, worksheet, user, user_id, bold, header_format, format_tittle):
		"""
			Funcion que permite generar el encabezado del informe de excel
		"""
		data_company = self.return_information_company()

		date_from = self.date_from
		date_to = self.date_to

		worksheet.set_column('A1:A1',35)
		worksheet.set_column('B1:B1',35)
		worksheet.set_column('C1:C1',25)
		worksheet.set_column('D1:D1',35)
		worksheet.set_column('E1:E1',50)
		worksheet.set_column('F1:F1',35)
		worksheet.set_column('G1:G1',30)
		worksheet.set_column('H1:H1',25)
		worksheet.set_column('I1:I1',25)
		worksheet.set_column('J1:J1',20)
		worksheet.set_column('K1:K1',20)
		worksheet.set_column('L1:L1',25)
		worksheet.set_column('M1:M1',30)
		worksheet.set_column('N1:N1',30)
		worksheet.set_column('O1:O1',30)
		worksheet.set_column('P1:P1',30)
		worksheet.set_column('Q1:Q1',30)
		worksheet.set_column('R1:R1',30)
		worksheet.set_column('S1:S1',30)

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
			name_report = 'Reporte de Comisiones' 
			preview = name_report 
			worksheet.merge_range('C3:D4',preview, format_tittle)
	
			row=12
			col=0

			now=fields.Datetime.context_timestamp(self, fields.Datetime.from_string(fields.Datetime.now()))
			date_today=fields.Date.context_today(self)
			date_create= str("Fecha Creacion")
			worksheet.write('G1', str(date_create), header_format)
			worksheet.write('G2', str(date_today), bold)
			worksheet.write('G4', 'Fecha Inicial', header_format)
			worksheet.write('G5', str(date_from), bold)
			worksheet.write('G6', 'Fecha Final', header_format)
			worksheet.write('G7', str(date_to), bold)



	def return_users(self, data_user):
		"""
			Permite retornar los usuarios para el reporte de comisiones
		"""
		data = []
		if data_user:
			for x in data_user:
				vals = {
					'user_id': x.id,
					'name': x.partner_id.name
				}
				data.append(vals)
		else:
			user_ids = self.env['res.users'].search([])
			if user_ids:
				for x in user_ids:
					vals = {
						'user_id': x.id,
						'name': x.partner_id.name
					}
					data.append(vals)
		return data

	@api.multi
	def generate_excel(self):
		"""
		Funcion que permite generar el excel
		"""
		data_user = self.return_users(self.user_ids)
		model_invoice = self.env['account.invoice']

		


		now=fields.Datetime.context_timestamp(self, fields.Datetime.from_string(fields.Datetime.now()))
		date_today=fields.Date.context_today(self)
		
		name_report = 'Reporte de Comisiones' 

		Header_Text = name_report
		file_data = BytesIO()
		workbook = xlsxwriter.Workbook(file_data)

		#Formato de letras y celdas
		bold = workbook.add_format({'bold': 1,'align':'left','border':1, 'font_size': 14})
		format_tittle = workbook.add_format({'bold': 1,'align':'center', 'valign':'vcenter', 'border':1, 'fg_color':'#F9CEA9', 'font_size': 25 })
		letter_gray_name = workbook.add_format({'align':'left', 'font_color': 'gray', 'indent':2, 'font_size': 14})
		letter_gray = workbook.add_format({'align':'right', 'font_color': 'gray', 'num_format': '$#,#0.0', 'font_size': 14})
		letter_black_name = workbook.add_format({'align':'left', 'font_color': 'black', 'font_size': 14})
		letter_black = workbook.add_format({'align':'right', 'font_color': 'black', 'num_format': '$#', 'font_size': 14})
		header_format = workbook.add_format({'bold': 1,'align':'center','valign':'vcenter', 'border':1, 'fg_color':'#F9CEA9', 'font_size': 18 })
		header_format_subtitle = workbook.add_format({'bold': 1,'align':'center','valign':'vcenter', 'border':1, 'fg_color':'#F9E9DB', 'font_size': 18 })

		bold_total = workbook.add_format({'align':'right', 'font_color': 'black', 'bold': 1, 'border':1, 'font_size': 14, 'num_format': '$#,#0.0'})
		bold_total_color = workbook.add_format({'align':'right', 'font_color': 'black', 'bold': 1, 'border':1, 'fg_color':'#E3E4E5', 'font_size': 18, 'fg_color':'#F9CEA9', 'num_format': '$#,#0.0'})
		bold_total_gray = workbook.add_format({'align':'right', 'font_color': 'black', 'bold': 1, 'border':1, 'fg_color':'#E3E4E5', 'font_size': 14, 'num_format': '$#,#0.0'})
		format_diag = workbook.add_format({'align':'left', 'font_color': 'black', 'bold': 1, 'fg_color':'#E3E4E5', 'font_size': 18, 'fg_color':'#F9CEA9'})

		for x in data_user:
			
			data = self.return_data_invoice(self.date_from, self.date_to, x['user_id'])
			if data:
				if self.validate_record_payments(data):
					worksheet = workbook.add_worksheet(str(x['name']) or 'Boot')
					self.generate_data_complete_excel(data, worksheet, x['user_id'], x['name'], model_invoice, bold, header_format, format_tittle, letter_black, bold_total, letter_black_name, bold_total_color, bold_total_gray, format_diag, header_format_subtitle)

		workbook.close()
		file_data.seek(0)

		self.write({'document':base64.encodestring(file_data.read()), 'filename':Header_Text + '  ' + str(self.date_from) + ' - ' + str(self.date_to) +'.xlsx'})


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
		result['date_to'] =  str(self.date_to)
		result['user_ids'] = [x.id for x in self.user_ids if self.user_ids] or None
		result['commission_vendor_conf_ids'] = self.return_data_commission(self.commission_vendor_conf_ids)
		#result['info_data'] = self.return_data()

		#print(result)
		return result

	def _print_report(self, data):
		"""
			Funcion que permite retornar el template del reporte
		"""
		return self.env.ref('invoice_commissions_vendor.action_report_invoice_comission_vendor').with_context(landscape=True).report_action(self, data=data)

	@api.multi
	def generate_pdf(self):
		"""
			Funcion que permite generar el reporte pdf general del dia
		"""
		self.ensure_one()
		

		data = {}
		data['ids'] = self.env.context.get('active_ids', [])
		data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
		data['form'] = self.read(['date_from', 'date_to','user_ids', 'commission_vendor_conf_ids'])[0]
		used_context = self._build_contexts(data)

		#data['form']['doctor_attention_ids'] = [x for x in self.doctor_attention_ids]
		data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang'))

		return self.with_context(discard_logo_check=True)._print_report(data)

CommissionVendor()