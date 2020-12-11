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

from xlrd import open_workbook
import base64


import openpyxl
from openerp import models, fields, api, _
from tempfile import TemporaryFile

class StockInvetoryInherit(models.Model):
	
	_inherit = 'stock.inventory'

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

	def return_filter_value(self, filter_value):
		value = ''
		if filter_value:
			if filter_value == 'none':
				value = "TODOS LOS PRODUCTOS"
			elif filter_value == 'category':
				value = "UNA CATEGORIA DE PRODUCTO"
			elif filter_value == 'product':
				value = "UN SOLO PRODUCTO"
			elif filter_value == 'partial':
				value = "SELECCIONAR PRODUCTOS MANUALMENTE"
			elif filter_value == 'owner':
				value = "UN SOLO PROPIETARIO"
			elif filter_value == 'product_owner':
				value = "UN PRODUCTO PARA UN PROPIETARIO ESPECIFICO"
			elif filter_value == 'lot':
				value = "NUMERO DE LOTE/SERIE"
			elif filter_value == 'pack':
				value = "UN PAQUETE"
			return value

	@api.multi
	def generate_excel(self):


		#name_report = "Ajuste de Inventario - " + str(fields.Datetime.from_string(fields.Datetime.now()))

		data_company = self.return_information_company()
		name_report = "ANALISIS DE DIFERENCIAS EN FISICO"
		format="%Y-%m-%d %H:%M:00"
		now=fields.Datetime.context_timestamp(self, fields.Datetime.from_string(fields.Datetime.now()))
		date_today=str(datetime.strftime(now, format))

		Header_Text = str(self.name).upper() + ' ' + str(date_today)
		file_data = BytesIO()
		workbook = xlsxwriter.Workbook(file_data)
		worksheet = workbook.add_worksheet(name_report)
	
		header_format = workbook.add_format({'bold': 1,'align':'center','valign':'vcenter', 'border':1, 'fg_color':'#f9770c', 'font_size': 18 })
		header_format_left = workbook.add_format({'bold': 1,'align':'left', 'border':1, 'fg_color':'#f9770c', 'font_size': 18 })
		
		format_tittle = workbook.add_format({'bold': 1,'align':'center', 'valign':'vcenter',  'fg_color':'#f9770c', 'font_size': 22 })
		letter_category = workbook.add_format({'bold': 1,'align':'center','valign':'vcenter', 'border':1, 'fg_color':'#F9CEA9', 'font_size': 16 })
		letter_pvt = workbook.add_format({'bold': 1,'align':'center','valign':'vcenter', 'border':1, 'fg_color':'#ffe8d8', 'font_size': 15 })
		letter_number_total = workbook.add_format({'bold': 1,'align':'right','valign':'vcenter', 'num_format': '$#,##0.00', 'border':1, 'fg_color':'#F9CEA9', 'font_size': 16 })
		
		letter_left = workbook.add_format({'align':'left', 'font_color': 'black', 'font_size': 14})
		letter_number = workbook.add_format({'align':'right', 'font_color': 'black', 'num_format': '$#,##0.00', 'font_size': 14})
		bold = workbook.add_format({'bold': 1,'align':'left','border':1, 'font_size': 14})

		worksheet.set_column('A1:A1',35)
		worksheet.set_column('B1:B1',55)
		worksheet.set_column('C1:C1',35)
		worksheet.set_column('D1:C1',35)
		worksheet.set_column('E1:E1',35)
		worksheet.set_column('F1:F1',35)
		worksheet.set_column('G1:G1',35)
		worksheet.set_column('H1:H1',35)
	

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


			worksheet.merge_range('C3:D3', data_company['name'].upper(), format_tittle)
			worksheet.merge_range('C4:D4',preview, format_tittle)
			worksheet.merge_range('C5:D5', "** POR ITEM **", format_tittle)

			worksheet.write('A10', 'FECHA', header_format_left)
			worksheet.write('B10', str(self.date), bold)

			worksheet.write('A11', 'BODEGA PRNCIPAL', header_format_left)
			worksheet.write('B11', ((self.location_id.location_id.name or '') + '/' + (self.location_id.name)).upper(), bold)

			worksheet.write('A12', 'USUARIO', header_format_left)
			worksheet.write('B12', str(self.env.user.partner_id.name).upper(), bold)

			worksheet.write('A13', 'INVENTARIO', header_format_left)
			worksheet.write('B13', str(self.name).upper(), bold)

			worksheet.write('A14', 'INVENTARIO DE', header_format_left)
			worksheet.write('B14', self.return_filter_value(self.filter), bold)

	

			worksheet.write('F1', 'FECHA', header_format_left)
			worksheet.write('G1', str(date_today)[:10], bold)
			worksheet.write('F2', 'HORA', header_format_left)
			worksheet.write('G2', str(date_today)[10:], bold)

			if len(self.line_ids) > 0:

				worksheet.write('A16', 'REFERENCIA', header_format)
				worksheet.write('B16', 'PRODUCTO', header_format)
				worksheet.write('C16', 'U.M', header_format)
				worksheet.write('D16', 'FISICO', header_format)
				worksheet.write('E16', 'EXISTENCIA', header_format)
				worksheet.write('F16', 'DIFERENCIA', header_format)
				worksheet.write('G16', 'COSTO UNITARIO', header_format)
				worksheet.write('H16', 'COSTO TOTAL', header_format)


				row=16
				col=0

				for value in self.line_ids:

					standard_price = value.product_id.standard_price
					default_code = str(value.product_id.default_code)
					
					worksheet.write(row,col, default_code if default_code != 'False' else "", letter_left)
					worksheet.write(row,col+1, str(value.product_id.name),letter_left)
					worksheet.write(row,col+2, str(value.product_uom_id.name),letter_left)
					worksheet.write(row,col+3, value.theoretical_qty,letter_number)
					worksheet.write(row,col+4, value.product_qty,letter_number)
					worksheet.write(row,col+5, value.diference,letter_number)
					worksheet.write(row,col+6, standard_price,letter_number)
					worksheet.write(row,col+7 , standard_price * value.diference, letter_number)
					row+=1

			workbook.close()
			file_data.seek(0)

			self.write({'document':base64.encodestring(file_data.read()), 'filename':Header_Text+'.xlsx'})




StockInvetoryInherit()