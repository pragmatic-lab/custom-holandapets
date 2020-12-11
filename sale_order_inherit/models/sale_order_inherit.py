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

from odoo import api, fields, models, _
import time
from datetime import datetime, timedelta, date
import logging
_logger = logging.getLogger(__name__)
from odoo import modules
from math import sqrt
import statistics as stats
import math
from odoo.http import request

class SaleOrderInherit(models.Model):

	_inherit = 'sale.order'

	sale_order_conf_text_id = fields.Many2one('sale.order_conf_text', string = "Configuración Reporte")
	total_round = fields.Boolean(string="Redondear Totales", help="Al estar seleccionado esta opcion permite redondear los totales")

	@api.model
	def _default_warehouse_id(self):
		company = self.env.user.company_id.id
		warehouse_default_id = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)

		warehouse_id = None
		if self.user_id:

			warehouse_id = self.user_id.warehouse_id.id

		if not warehouse_id:
			warehouse_id = warehouse_default_id

		return self.user_id.warehouse_id.id


	def validate_create_quick_invoice(self):
		"""
			Funcion que permite validar si se puede crear o no la factura rapida
		"""
		if self.env.user.has_group('sale_order_inherit.group_create_invoice_quick_configuration'):
			return  True
		
		return False


	@api.multi
	def button_quick_create_invoice_complete(self):
		"""
			Funcion que permite crear una factura al confirmar una venta, confirmar el stock picking y abrir la factura inmeditamente
		"""
		if self.validate_create_quick_invoice():
			imediate_obj=self.env['stock.immediate.transfer']
			for order in self:

				order.action_confirm()

				warehouse=order.warehouse_id

				for picking in self.picking_ids:
					picking.action_confirm()
					picking.action_assign()


					imediate_rec = imediate_obj.create({'pick_ids': [(4, order.picking_ids.id)]})
					imediate_rec.process()
					if picking.state !='done':
						for move in picking.move_ids_without_package:
							move.quantity_done = move.product_uom_qty
						picking.button_validate()

				self._cr.commit()

				order.action_invoice_create()  

				return order.action_view_invoice()


	@api.multi
	def button_quick_create_invoice(self):
		"""
			Funcion que permite crear una factura al confirmar una venta, como tambien abrir la factura inmeditamente
		"""
		if self.validate_create_quick_invoice():
			for order in self:
				order.action_confirm()			
				order.action_invoice_create()  

				return order.action_view_invoice()

	@api.depends('order_line')
	@api.onchange('order_line')
	def onchange_order_line_validate_partner(self):

		"""
			Funcion que permite cargar un partner configurado automaticamente, se usa cuando la venta no tiene cliente
		"""

		if self.order_line:
			partner_id = self.env.ref('sale_order_inherit.partner_sales_debit')
			if partner_id:

				if not self.partner_id:

					self.partner_id =  partner_id.id
					self.onchange_partner_id()


	def validate_number_phone(self, data):
		if data.phone and data.mobile:
			return data.phone + ' - ' + data.mobile
		if data.phone and not data.mobile:
			return data.phone
		if data.mobile and not data.phone:
			return data.mobile


	def validate_state_city(self, data):
		return ((data.country_id.name + ' ') if data.country_id.name else ' ') + ( ' ' + (data.state_id.name + ' ') if data.state_id.name else ' ') + (' ' + data.xcity.name if data.xcity.name else '')


	"""
	@api.model
	def create(self, vals):

		if 'partner_id' not in vals:
			partner_id = self.env.ref('sale_order_inherit.partner_sales_debit')
			if partner_id:

				vals['partner_id'] =  partner_id.id
		res = super(SaleOrderInherit, self).create(vals)

		return res

	"""

	@api.model
	def default_get(self, default_fields):
		"""
			Funcion que nos sirve para cargar datos por defecto
				-> Impresion del reporte
				-> Lista de precios
		"""

		conf_id = self.env['sale.order_conf_text'].search([('code', '=', '12345')], limit=1)
		pricelist_id = self.env['product.pricelist'].search([('pricelist_default', '=', True)], limit=1)
		payment_term_id = self.env.ref('account.account_payment_term_immediate')
		partner_id = self.env.ref('sale_order_inherit.partner_sales_debit')


		res= super(SaleOrderInherit, self).default_get(default_fields)

		if partner_id:
			res['partner_id'] = partner_id.id

		if conf_id:
			res['sale_order_conf_text_id'] = conf_id.id

		if pricelist_id:
			res['pricelist_id'] = pricelist_id.id

		#if payment_term_id:
		#	res['payment_term_id'] = 1

		company = self.env.user.company_id.id
		warehouse_default_id = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1).id

		warehouse_id = None

		user_id = self.env['res.users'].search([('id', '=', self.env.user.id)], limit=1)
		if user_id.warehouse_id:
			warehouse_id = user_id.warehouse_id.id

		if not warehouse_id:
			warehouse_id = warehouse_default_id

		res['warehouse_id'] = warehouse_id

		return res


	def update_picking(self, val):

		picking_ids = self.env['stock.picking'].search([('state', '=', 'assigned'), ('picking_type_id', '=', 2)])
		imediate_obj=self.env['stock.immediate.transfer']
		_logger.info('los picking son: ' + str(len(picking_ids)))

		flag = 1
		if picking_ids:
			for x in picking_ids:
				if flag <= val:
					_logger.info(x.id)
					if len(x.sale_id.picking_ids) == 1:
						for picking in x.sale_id.picking_ids:

							picking.action_confirm()
							picking.action_assign()

							_logger.info(x.sale_id.picking_ids)

							
							imediate_rec = imediate_obj.create({'pick_ids': [(4, x.sale_id.picking_ids.id)]})
							imediate_rec.process()
							if picking.state !='done':
								for move in picking.move_ids_without_package:
									move.quantity_done = move.product_uom_qty
								picking.button_validate()
				flag +=1

				#self._cr.commit()



				"""
				imediate_rec = imediate_obj.create({'pick_ids': [(4, order.picking_ids.id)]})
				imediate_rec.process()
				if picking.state !='done':
					for move in picking.move_ids_without_package:
						move.quantity_done = move.product_uom_qty
					picking.button_validate()

				self._cr.commit()
				"""


	def cancel_all_sale_order(self):
		"""
			Funcion que permite cancelar las ordenes de venta, se ejecuta una accion programada cada 7 dias
		"""
		today = datetime.today()
		date_update = today + timedelta(days=-7)
		sale_order_ids = self.search([('state', '=', 'draft'), ('create_date', '<', str(date_update))])
		if sale_order_ids:
			for x in sale_order_ids:
				if x.state == 'draft':
					x.action_cancel()


	def _prepare_invoice(self):
		vals = super(SaleOrderInherit, self)._prepare_invoice()

		vals.update({
			'date_invoice_complete': self.date_order,
			'date_invoice': str(self.date_order)[:10]
		})

		if self.return_validate_day_iva():
			vals.update({
			'active_day_iva': self.active_day_iva,
			'type_payment': self.type_payment,
			'html_active_amount_day': self.html_active_amount_day
		})
		return vals

	def update_sale_order_holanda(self, intial, final):

		sale_order_ids = self.search([])


		if sale_order_ids:
			for x in rang(intial, final):
				sale_order = sale_order_ids[x]
				if sale_order:
					sale_order._amount_all()



SaleOrderInherit()