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

class SaleOrderInherit(models.Model):
	_inherit = 'sale.order'

	taxes_ids = fields.One2many('sale.order.tax', 'order_id', string='Impuestos', compute='_compute_sale_order_taxes', store=True)

	@api.multi
	def return_data_taxes_order_line(self, order):
		tax_grouped = {}
		currency = order.currency_id or order.company_id.currency_id
		if order.order_line:
			for line in order.order_line:
				price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
				taxes = line.tax_id.compute_all(price_reduce, quantity=line.product_uom_qty, product=line.product_id, partner=order.partner_shipping_id)['taxes']

				for tax in taxes:
					val = {
						'order': order.id,
						'name': tax['name'],
						'amount': tax['amount'],
						'base': currency.round(tax['base'] * line.product_uom_qty),
						'sequence': tax['sequence']
					}
					key = (val['name'])
					if key not in tax_grouped:
						tax_grouped[key] = val
					else:
						tax_grouped[key]['base'] += val['base']
						tax_grouped[key]['amount'] += val['amount']

			for t in tax_grouped.values():
				t['base'] = currency.round(t['base'])
				t['amount'] = currency.round(t['amount'])
		return tax_grouped


	@api.multi
	@api.depends('order_line')
	def _compute_sale_order_taxes(self):

		data = []
		for order in self:

			for tax in self.return_data_taxes_order_line(order).values():

				vals = {
					'sequence': tax['sequence'],
					'name': tax['name'],
					'base': tax['base'],
					'amount': tax['amount']}
				data.append((0, 0, vals))

		self.taxes_ids = data

SaleOrderInherit()






