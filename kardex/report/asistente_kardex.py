# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import time
import datetime
import xlwt
import base64
import io
import logging
import logging
_logger = logging.getLogger(__name__)

class AsistenteKardex(models.TransientModel):
	_name = 'kardex.asistente_kardex'
	_description = 'Kardex'

	def _default_producto(self):
		if len(self.env.context.get('active_ids', [])) > 0:
			return self.env.context.get('active_ids')[0]
		else:
			return None

	ubicacion_id = fields.Many2one("stock.location", string="Ubicacion", required=True)
	producto_ids = fields.Many2many("product.product", string="Productos", required=True)
	fecha_desde = fields.Datetime(string="Fecha Inicial", required=True)
	fecha_hasta = fields.Datetime(string="Fecha Final", required=True)
	archivo_excel = fields.Binary('Archivo excel')
	name_excel = fields.Char('Nombre archivo', default='kardex.xls', size=32)

	@api.multi
	def print_report(self):
		data = {
			 'ids': [],
			 'model': 'kardex.asistente_kardex',
			 'form': self.read()[0]
		}
		return self.env.ref('kardex.action_reporte_kardex').report_action(self, data=data)

	@api.multi
	def reporte_excel(self):
		libro = xlwt.Workbook()
		hoja = libro.add_sheet('reporte')

		xlwt.add_palette_colour("custom_colour", 0x21)
		libro.set_colour_RGB(0x21, 200, 200, 200)
		estilo = xlwt.easyxf('pattern: pattern solid, fore_colour custom_colour')
		


		value_style_header = xlwt.easyxf("font: bold on, height 300, name Arial; alignment: horizontal center ,vertical center; borders: top thin,right thin,bottom thin,left thin")
		header_bold = xlwt.easyxf("font: bold on, height 200; pattern: pattern solid, fore_colour gray25;alignment: horizontal center ,vertical center")
		header_bold_data = xlwt.easyxf("font: bold on, height 250; pattern: pattern solid, fore_colour gray25; alignment: horizontal left ,vertical center;  borders: top thin,right thin,bottom thin,left thin")
				
		hoja.write(0, 0, 'KARDEX', value_style_header)
		datos = {}
		datos['fecha_desde'] = self.fecha_desde
		datos['fecha_hasta'] = self.fecha_hasta
		datos['ubicacion_id'] = []
		datos['ubicacion_id'].append(self.ubicacion_id.id)
		
		y = 2
		hoja.col(0).width = 4200
		hoja.col(1).width = 4200
		hoja.col(2).width = 7000
		hoja.col(3).width = 4200
		hoja.col(4).width = 4200
		hoja.col(5).width = 4200

		for producto in self.producto_ids:

			resultado = self.env['report.kardex.reporte_kardex'].lineas(datos, producto.id)
			hoja.write(y, 0, 'Fecha desde:', header_bold_data)
			hoja.write(y, 1, 'Fecha hasta:', header_bold_data)
			hoja.write(y, 2, 'Ubicación:', header_bold_data)
			hoja.write(y, 3, 'Producto:', header_bold_data)
			hoja.write(y, 4, 'Inicial:', header_bold_data)
			hoja.write(y, 5, 'Entradas:', header_bold_data)
			hoja.write(y, 6, 'Salidas:', header_bold_data)
			hoja.write(y, 7, 'Final:', header_bold_data)

			y += 1
			hoja.write(y, 0, datetime.datetime.strftime(self.fecha_desde,'%d/%m/%Y'))
			hoja.write(y, 1, datetime.datetime.strftime(self.fecha_hasta,'%d/%m/%Y'))
			hoja.write(y, 2, self.ubicacion_id.display_name)
			hoja.write(y, 3, producto.name)
			hoja.write(y, 4, resultado['totales']['inicio'])
			hoja.write(y, 5, resultado['totales']['entrada'])
			hoja.write(y, 6, resultado['totales']['salida'])
			hoja.write(y, 7, resultado['totales']['inicio']+resultado['totales']['entrada']+resultado['totales']['salida'])
			y += 2
			hoja.write(y, 0, 'Fecha', header_bold_data)
			hoja.write(y, 1, 'Documento', header_bold_data)
			hoja.write(y, 2, 'Empresa', header_bold_data)
			hoja.write(y, 3, 'Tipo', header_bold_data)
			hoja.write(y, 4, 'UOM', header_bold_data)
			hoja.write(y, 5, 'Entradas', header_bold_data)
			hoja.write(y, 6, 'Salidas', header_bold_data)
			hoja.write(y, 7, 'Final', header_bold_data)
			hoja.write(y, 8, 'Costo', header_bold_data)
			hoja.write(y, 9, 'Total', header_bold_data)
			y += 1
			for linea in resultado['lineas']:
				hoja.write(y, 0, datetime.datetime.strftime(linea['fecha'],'%d/%m/%Y'))
				hoja.write(y, 1, linea['documento'])
				hoja.write(y, 2, linea['empresa'])
				hoja.write(y, 3, linea['tipo'])
				hoja.write(y, 4, linea['unidad_medida'])
				hoja.write(y, 5, linea['entrada'])
				hoja.write(y, 6, linea['salida'])
				hoja.write(y, 7, linea['saldo'])
				hoja.write(y, 8, linea['costo'])
				hoja.write(y, 9, linea['saldo'] * linea['costo'])
				y += 1
			y += 1

		f = io.BytesIO()
		libro.save(f)
		datos = base64.b64encode(f.getvalue())
		self.write({'archivo_excel':datos, 'name_excel':'kardex.xls'})

		return {
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'kardex.asistente_kardex',
			'res_id': self.id,
			'view_id': False,
			'type': 'ir.actions.act_window',
			'target': 'new',
		}


	@api.multi
	def return_view_data(self):


		data = []

		values_sql = ""

		datos = {}
		datos['fecha_desde'] = self.fecha_desde
		datos['fecha_hasta'] = self.fecha_hasta
		datos['ubicacion_id'] = []
		datos['ubicacion_id'].append(self.ubicacion_id.id)

		for producto in self.producto_ids:
			resultado = self.env['report.kardex.reporte_kardex'].lineas(datos, producto.id)

			for linea in resultado['lineas']:

				vals= {
					'date_begin': self.fecha_desde,
					'date_end': self.fecha_hasta,
					'ubicacion_id': self.ubicacion_id.id,
					'product_id': producto.id,
					'inventory_initial': resultado['totales']['inicio'],
					'inventory_in': resultado['totales']['entrada'],
					'inventory_out': resultado['totales']['salida'],
					'inventory_final': resultado['totales']['inicio']+resultado['totales']['entrada']+resultado['totales']['salida'],
					'date_move': linea['fecha'],
					'document': linea['documento'],
					'partner_id': linea['partner_id'],
					'type_move': linea['tipo'],
					'inventory_move_in': linea['entrada'],
					'inventory_move_out': linea['salida'],
					'inventory_saldo': linea['saldo'],
					'standard_price': linea['costo'],
					'total': linea['saldo'] * linea['costo'],
				}
				data.append(vals)
				partner_id = linea['partner_id'] if linea['partner_id'] else 'null'
				values_sql += '(' + "'" + str(self.fecha_desde) + "', '" + str(self.fecha_hasta) + "', " + str(self.ubicacion_id.id) + ", " + str(producto.id) + ", " + str(resultado['totales']['inicio']) + ", " + str(resultado['totales']['entrada']) + ", " + str(resultado['totales']['salida']) + ", " + str(resultado['totales']['inicio']+resultado['totales']['entrada']+resultado['totales']['salida']) + ", '" + str(linea['fecha']) + "', '" + str(linea['documento']) + "', " + str(partner_id) + ", '" + str(linea['tipo']) + "', " + str(linea['entrada']) + ", " + str(linea['salida']) + ", " + str(linea['saldo']) + ", " + str(linea['costo']) + ", " + str(linea['saldo'] * linea['costo']) + '),'

		sql_delete = """
			DELETE FROM report_kardex_lines
		"""
		self.env.cr.execute(sql_delete)

		sql_insert = """
			INSERT INTO report_kardex_lines (date_begin, date_end, ubicacion_id, product_id, inventory_initial, inventory_in, inventory_out, inventory_final, date_move, document, partner_id, type_move, inventory_move_in, inventory_move_out, inventory_saldo, standard_price, total) VALUES
			"""

		sql_insert = sql_insert + values_sql[:len(values_sql)-1]

		_logger.info(sql_insert)
		self.env.cr.execute(sql_insert)

		context = self.env.context.copy()
		context.update( {  'search_default_product': True, 'search_default_type_move_inventory': True} ) 
		self.env.context = context


		return {
			'name': _('Reporte Kardex'),
			'res_model':'report.kardex.lines',
			'type':'ir.actions.act_window',
			'view_mode': 'tree',
			'view_type': 'form',
			'context': context
		}	

