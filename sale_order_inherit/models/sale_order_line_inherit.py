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

class SaleOrderLineInherit(models.Model):

	_inherit = 'sale.order.line'

	warehouse_quantity = fields.Char(compute='_get_warehouse_quantity', string='Ctdad Stock', store=True)

	@api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
	def _compute_amount(self):
		"""
		Compute the amounts of the SO line.
		"""
		super(SaleOrderLineInherit, self)._compute_amount()
		for line in self:
			price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
			taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
			line.update({
				'price_tax': round(sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))),
				'price_total': round(taxes['total_included']),
				'price_subtotal': round(taxes['total_excluded']),
			})

	def validate_change_price(self):
		"""
			Funcion que permite validar si se puede cambiar el precio o no en la venta
		"""
		if self.env.user.has_group('sale_order_inherit.group_modifcate_price_sales'):
			return True
		return False

	@api.onchange('price_unit')
	def onchange_product_price_unit(self):

		if not self.validate_change_price():
			self.product_id_change()

	@api.depends('product_id')
	def _get_warehouse_quantity(self):
		"""
			Funcion que permite conocer el stock actual del producto en todos los almacenes disponibles
		"""
		for record in self:
			warehouse_quantity_text = ''
			product_id = self.env['product.product'].sudo().search([('id', '=', record.product_id.id)])
			if product_id:
				quant_ids = self.env['stock.quant'].sudo().search([('product_id','=',product_id[0].id),('location_id.usage','=','internal')])
				t_warehouses = {}
				for quant in quant_ids:
					if quant.location_id:
						if quant.location_id not in t_warehouses:
							t_warehouses.update({quant.location_id:0})
						t_warehouses[quant.location_id] += quant.quantity

				tt_warehouses = {}
				for location in t_warehouses:
					warehouse = False
					location1 = location
					while (not warehouse and location1):
						warehouse_id = self.env['stock.warehouse'].sudo().search([('lot_stock_id','=',location1.id)])
						if len(warehouse_id) > 0:
							warehouse = True
						else:
							warehouse = False
						location1 = location1.location_id
					if warehouse_id:
						if warehouse_id.name not in tt_warehouses:
							tt_warehouses.update({warehouse_id.name:0})
						tt_warehouses[warehouse_id.name] += t_warehouses[location]

				for item in tt_warehouses:
					if tt_warehouses[item] != 0:
						warehouse_quantity_text = warehouse_quantity_text + ' ** ' + item + ': ' + str(tt_warehouses[item])

				record.warehouse_quantity = str(warehouse_quantity_text[3:])

				


	@api.depends('product_id')
	@api.onchange('product_id')
	def onchange_warehouse_quantityy(self):

		for record in self:
			warehouse_quantity_text = ''
			product_id = self.env['product.product'].sudo().search([('id', '=', record.product_id.id)])
			if product_id:
				quant_ids = self.env['stock.quant'].sudo().search([('product_id','=',product_id[0].id),('location_id.usage','=','internal')])
				t_warehouses = {}
				for quant in quant_ids:
					if quant.location_id:
						if quant.location_id not in t_warehouses:
							t_warehouses.update({quant.location_id:0})
						t_warehouses[quant.location_id] += quant.quantity

				tt_warehouses = {}
				for location in t_warehouses:
					warehouse = False
					location1 = location
					while (not warehouse and location1):
						warehouse_id = self.env['stock.warehouse'].sudo().search([('lot_stock_id','=',location1.id)])
						if len(warehouse_id) > 0:
							warehouse = True
						else:
							warehouse = False
						location1 = location1.location_id
					if warehouse_id:
						if warehouse_id.name not in tt_warehouses:
							tt_warehouses.update({warehouse_id.name:0})
						tt_warehouses[warehouse_id.name] += t_warehouses[location]

				for item in tt_warehouses:
					if tt_warehouses[item] != 0:
						warehouse_quantity_text = warehouse_quantity_text + ' ** ' + item + ': ' + str(tt_warehouses[item])
				
				record.warehouse_quantity = str(warehouse_quantity_text[3:])
				self.warehouse_quantity = str(warehouse_quantity_text[3:])


	def rounded_number_fix_price(self, price_product_final):

		number = round(price_product_final)

		print('********')
		print(number)
		
		umil = number / 1000
		tmp = number % 1000
		decenas = tmp % 100
		print(decenas)

		#redondear a 0
		if decenas < 50:
			price_product_final = number - decenas

		if decenas > 50:
			price_product_final = number + (100 - decenas)

		return price_product_final



	def calculate_price_avarege(self, product):
		supplier_ids = self.product_id.seller_ids

		#print(supplier_ids)
		#supplierinfo_id = self.env['product.supplierinfo'].search([('id', 'in', [x.id for x in supplier_ids])], order='id desc')
		#print(supplierinfo_id)
		percent_amount_supplier = 0
		price_product_final = 0

		standard_price = self.product_id.standard_price
			
		price_pricelist = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id) 
		
		print('el precio lista seria: ' + str(price_pricelist))


		if standard_price > 0 and price_pricelist > 0:
			pricelist_percent = (((price_pricelist/standard_price)*100) - 100) #se calcula por la categoria se asemeja que es el 15%
			print('esto es la vaina')
			print(pricelist_percent)

			#supplier_id = supplierinfo_id[0]
			product_brand_percent = product.product_tmpl_id.product_brand_id.percentage_price # se espera un 5%
			#price_supplier = self.env['account.tax']._fix_tax_included_price_company(supplier_id.price, self.product_id.supplier_taxes_id, self.tax_id, self.company_id)
			#print('el porcentaje seria: ' + str(product_brand_percent))
			if product_brand_percent > 0:
				
				#print('el costo del producto es:')
				#print(standard_price)
				percent_total = (pricelist_percent + product_brand_percent)/100 #0.20
				#print(percent_total)

				value_apply = (1 - percent_total) #0.80

				price_product_final = standard_price / value_apply
				#print(price_product_final)

				#validamos que impuestos tienen los productos predefinidos
				fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
				# If company_id is set, always filter taxes by the company
				taxes = self.product_id.taxes_id.filtered(lambda r: not self.company_id or r.company_id == self.company_id)
				taxes_ids = fpos.map_tax(taxes, self.product_id, self.order_id.partner_shipping_id) if fpos else taxes

				#print(taxes_ids)


				tota_taxes = 0

				if taxes_ids:
					for x in taxes_ids:
						tota_taxes += price_product_final * ( (x.amount)/100 )

				#print('total taxes ' + str(tota_taxes))
				#print(price_product_final)

				price_product_final = price_product_final + tota_taxes
				#print('precio final: ' + str(price_product_final))
				price_product_final = self.rounded_number_fix_price(price_product_final)


				#price_round = round(price_product_final)


				#remainder = round(price_round, -2)
				#total_price = 50 - (price_round - remainder)
				#price_product_final = price_round + total_price 
	
					
		return price_product_final



	@api.onchange('product_uom', 'product_uom_qty', 'product_id')
	def product_uom_change(self):

		if not self.product_uom or not self.product_id:
			self.price_unit = 0.0
			return

		if self.order_id.pricelist_id and self.order_id.partner_id:
			product = self.product_id.with_context(
				lang=self.order_id.partner_id.lang,
				partner=self.order_id.partner_id,
				quantity=self.product_uom_qty,
				date=self.order_id.date_order,
				pricelist=self.order_id.pricelist_id.id,
				uom=self.product_uom.id,
				fiscal_position=self.env.context.get('fiscal_position')
			)

			price_product_final = self.calculate_price_avarege(product)

			if price_product_final > 0:
				self.price_unit = price_product_final
			else:
				price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
				price_unit_fexed = self.rounded_number_fix_price(price_unit)
				self.price_unit = price_unit_fexed

			
			if self.order_id.return_validate_day_iva():
				if self.order_id.amount_untaxed < self.order_id.return_amount_day_iva():

					if price_product_final > 0:
						price = price_product_final * (1 - (self.discount or 0.0) / 100.0)
						taxes = self.tax_id.compute_all(price, self.order_id.currency_id, 1, product=self.product_id, partner=self.order_id.partner_shipping_id)
						_logger.info(taxes)
						if self.order_id.type_payment == 'bank':
							self.price_unit = taxes['total_excluded']
						else:
							self.price_unit = price_product_final
					else:
						price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
						price_unit_fexed = self.rounded_number_fix_price(price_unit)
						price = price_unit_fexed * (1 - (self.discount or 0.0) / 100.0)
						taxes = self.tax_id.compute_all(price, self.order_id.currency_id, 1, product=self.product_id, partner=self.order_id.partner_shipping_id)
						_logger.info(taxes)
						if self.order_id.type_payment == 'bank':
							self.price_unit = taxes['total_excluded']
						else:
							self.price_unit = price_unit_fexed
						#self.price_unit = taxes['total_excluded']

			else:			

				if price_product_final > 0:
					self.price_unit = price_product_final
				else:
					price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
					price_unit_fexed = self.rounded_number_fix_price(price_unit)
					self.price_unit = price_unit_fexed
			#"""





	@api.multi
	@api.onchange('product_id')
	def product_id_change(self):

		res = super(SaleOrderLineInherit, self).product_id_change()

		if self.order_id.return_validate_day_iva():

			print('estamos entrando')
			if self.order_id.amount_untaxed < self.order_id.return_amount_day_iva():

				price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
				taxes = self.tax_id.compute_all(price, self.order_id.currency_id, self.product_uom_qty, product=self.product_id, partner=self.order_id.partner_shipping_id)
	
				#self.price_unit = taxes['total_excluded']
		#self.tax_id = [(6, _, self.order_id.update_taxes(self.product_id))]
		return res
SaleOrderLineInherit()
