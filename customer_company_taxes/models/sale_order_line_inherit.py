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

	taxes_collected_id = fields.Many2one('taxes.collected', string = "Pago Impuestos")


	@api.onchange('taxes_collected_id', 'product_uom_qty')
	def onchange_taxes_collected(self):
		_logger.info('entrando al onchange')
		if self.taxes_collected_id:
			self.price_unit = 0


	@api.multi
	def _prepare_invoice_line(self, qty):
		"""
		Prepare the dict of values to create the new invoice line for a sales order line.

		:param qty: float quantity to invoice
		"""
		self.ensure_one()
		res = {}
		account = self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id

		if not account and self.product_id:
			raise UserError(_('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') %
				(self.product_id.name, self.product_id.id, self.product_id.categ_id.name))

		fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
		if fpos and account:
			account = fpos.map_account(account)

		res = {
			'name': self.name,
			'sequence': self.sequence,
			'origin': self.order_id.name,
			'account_id': account.id,
			'price_unit': self.price_unit,
			'quantity': qty,
			'taxes_collected_id': self.taxes_collected_id.id or False,
			'discount': self.discount,
			'uom_id': self.product_uom.id,
			'product_id': self.product_id.id or False,
			'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
			'account_analytic_id': self.order_id.analytic_account_id.id,
			'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
			'display_type': self.display_type,
		}


		return res

	def return_price_to_pay(self):
		"""
			Funcion que permite retornar el valor del impuesto del producto seleccionado, permitiendo de esta manera calcularlo
			aun con el precio del producto en 0
		"""
		price_tax = 0
		for line in self:
			if line.product_id:
				if line.order_id.pricelist_id:
					if line.taxes_collected_id:

						price_product = line.order_id.pricelist_id.price_get(line.product_id.id, line.product_uom_qty, None)
						for x in price_product:
							price_unit = price_product.get(x)

						if line.price_unit ==0:

								
							print('Cargando solo impuesto del producto')
							print(price_unit)
							taxes = line.tax_id.compute_all(price_unit, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
							price_tax = sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])) 
							
		_logger.info('el precio es: {}'.format(price_tax))
		return price_tax




	# @api.depends('product_uom_qty', 'taxes_collected_id', 'discount', 'price_unit', 'tax_id')
	# def _compute_amount(self):

	# 	price_tax = self.return_price_to_pay() or 0
	# 	flag = False
	# 	for line in self:
	# 		if line.taxes_collected_id:
	# 			line.price_unit = 0
	# 			flag = True

	# 		price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
	# 		taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
			
	# 		if not flag:
	# 			price_tax = 0
	# 		line.update({
	# 			'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])) + price_tax,
	# 			'price_total': taxes['total_included'] + price_tax,
	# 			'price_subtotal': taxes['total_excluded'],
	# 		})

SaleOrderLineInherit()