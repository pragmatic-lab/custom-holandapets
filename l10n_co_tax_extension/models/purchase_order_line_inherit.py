# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
#                                                                             #
# Part of Odoo. See LICENSE file for full copyright and licensing details.    #
#                                                                             #
#                                                                             #
#                                                                             #
# Co-Authors    Odoo LoCo                                                     #
#               Localización funcional de Odoo para Colombia                  #
#                                                                             #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################


from odoo import api, fields, models, _

import time
import odoo.addons.decimal_precision as dp
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError, AccessError
from odoo.tools.misc import formatLang
from odoo.addons import decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)


class PurchaseOrderInherit(models.Model):
	_inherit = 'purchase.order'


	wh_taxes = fields.Float(string="Retenciones", store=True, compute="amount_wh_taxes")
	taxes_ids = fields.One2many('purchase.order.tax', 'order_id', string='Impuestos', compute='_compute_sale_order_taxes', store=True)

	@api.model
	def return_data_wh_taxes(self):
		"""
			Funcion que permite retornar los impuestos anteriormente configurados en la posicion fiscal,
			para mostrar la data de los impuestos de las retenciones
		"""
		data=[]
		flag= False

		if self.date_order:
			date= datetime.strptime(str(self.date_order)[:10], '%Y-%m-%d').date()
			
			fiscal_position = self.fiscal_position_id

			if fiscal_position:

				if fiscal_position.tax_ids_invoice:

					for x in fiscal_position.tax_ids_invoice:

						if x.tax_id:

							flag=self.validate_type(x.tax_id, 'purchase', date)

							if flag:
								data.append(x.tax_id.id)

		#data contiene las retenciones que fueron establecidas en la posicion fiscal
		return data


	@api.one
	@api.depends('order_line.price_total')
	def amount_wh_taxes(self):
		"""
		Compute the total amounts of the SO.
		"""

		#_logger.info('**************************************')
		for order in self:
			#_logger.info('la data es')
			data_wh_taxes = order.return_data_wh_taxes()
			#_logger.info(data_wh_taxes)
			
			#suma total de impuestos
			sum_amount_total = sum(line.amount for line in order.taxes_ids if line.tax_id.id not in data_wh_taxes)
			
			#suma de retenciones
			sum_wh_taxes = 0

			if order.fiscal_position_id:
			
				#suma de retenciones
				if data_wh_taxes:
					sum_wh_taxes = sum(line.amount for line in order.taxes_ids if line.tax_id.id in data_wh_taxes)
					#_logger.info('las retenciones suman:')
					#_logger.info(sum_wh_taxes)

			amount_untaxed = amount_tax = 0.0
			for line in order.order_line:
				amount_untaxed += line.price_subtotal
				amount_tax += line.price_tax

			amount_tax -= sum_wh_taxes
			sum_wh_taxes = abs(sum_wh_taxes)
			order.update({
				'amount_untaxed': amount_untaxed,
				'amount_tax': sum_amount_total,
				'amount_total': amount_untaxed + sum_amount_total,
				'wh_taxes': sum_wh_taxes

			})


	@api.multi
	def return_data_taxes_order_line(self, order):
		tax_grouped = {}
		currency = order.currency_id or order.company_id.currency_id
		if order.order_line:
			for line in order.order_line:
				price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
				taxes = line.taxes_id.compute_all(price_reduce, quantity=line.product_qty, product=line.product_id, partner=order.partner_id)['taxes']

				for tax in taxes:
					
					val = {
						'order': order.id,
						'tax_id': tax['id'],
						'name': tax['name'],
						'amount': tax['amount'],
						'base': currency.round(tax['base'] * line.product_uom_qty),
						'sequence': tax['sequence']
					}
					key = (val['tax_id'])
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
					'tax_id': tax['tax_id'],
					'name': tax['name'],
					'base': tax['base'],
					'amount': tax['amount']}
				data.append((0, 0, vals))

		self.taxes_ids = data



	@api.multi
	def update_records_order_create_write(self, order_line):
		if order_line:
			for x in order_line:
				if x.product_id:
					x.taxes_id = [(6, _, self.update_taxes(x.product_id))]
					x.write({'taxes_id': [(6, _, self.update_taxes(x.product_id))]})

	@api.multi
	def update_records_order_line(self):

		self.update_records_order_create_write(self.order_line)
		self._compute_sale_order_taxes()


	def validate_type(self, record, type_tax_use, date_record):
		"""
			Funcion que permite validar si el valor de la venta es superior al impuesto configurado para poderlo aplicar
		"""

		if record.type_tax_use == type_tax_use:
			if record.base_taxes:

				for y in record.base_taxes:

					if y.start_date and y.end_date:

						if datetime.strptime(str(y.start_date), '%Y-%m-%d').date() >= date_record or date_record <= datetime.strptime(str(y.end_date), '%Y-%m-%d').date():
			
							sum_total = sum(x.price_subtotal for x in self.order_line if self.order_line)

							if sum_total >= y.amount:
							
								return True

		return False

	def update_taxes(self, product_id):
		"""
			Funcion que permite retornar los impuestos anteriormente configurados en la posicion fiscal,
			para mostrar en el campo de los impuestos de la factura
		"""
		data=[]
		flag= False

		date= datetime.strptime(str(self.date_order)[:10], '%Y-%m-%d').date()

		fiscal_position = self.fiscal_position_id

		if fiscal_position:

			if fiscal_position.tax_ids_invoice:

				for x in fiscal_position.tax_ids_invoice:
					if x.tax_id:

						#ventas de cliente
						flag = self.validate_type(x.tax_id, 'purchase', date)

						if flag:
							data.append(x.tax_id.id)

		if product_id:
			#validamos que impuestos tienen los productos predefinidos
			fpos = self.fiscal_position_id or self.partner_id.property_account_position_id
			# If company_id is set, always filter taxes by the company
			taxes = product_id.supplier_taxes_id.filtered(lambda r: not self.company_id or r.company_id == self.company_id)
			taxes_id = fpos.map_tax(taxes, product_id, self.partner_id) if fpos else taxes

			if product_id.without_retention:

				data_product = []
				if taxes_id:

					for x in product_id.supplier_taxes_id:
						data_product.append(x.id)

					return data_product

				#self.taxes_id= [(6, _, data_product)]
			else:

				if taxes_id:

					for x in product_id.supplier_taxes_id:
						data.append(x.id)
					return data

					#self.taxes_id= [(6, _, data)]

PurchaseOrderInherit()


class PurchaseOrderLineInherit(models.Model):

	_inherit = 'purchase.order.line'

	@api.onchange('price_unit', 'product_qty')
	def onchange_calculate_tax(self):
		"""
			Funcion que permite cargar los impuestos configurados en la posicion fiscal
		"""
		if self.order_id.fiscal_position_id and self.product_id:
			#_logger.info('esto es lo que trae')
			#_logger.info(self.order_id.update_taxes(self.product_id))
			self.taxes_id = [(6, _, self.order_id.update_taxes(self.product_id))] 


	@api.onchange('product_id')
	def onchange_product_id(self):
		result = {}

		if not self.product_id:
			return result

		# Reset date, price and quantity since _onchange_quantity will provide default values
		self.date_planned = datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
		self.price_unit = self.product_qty = 0.0
		self.product_uom = self.product_id.uom_po_id or self.product_id.uom_id
		result['domain'] = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}

		product_lang = self.product_id.with_context(
			lang=self.partner_id.lang,
			partner_id=self.partner_id.id,
		)
		self.name = product_lang.display_name
		if product_lang.description_purchase:
			self.name += '\n' + product_lang.description_purchase

		fpos = self.order_id.fiscal_position_id
		if self.env.uid == SUPERUSER_ID:
			company_id = self.env.user.company_id.id
			
			self.taxes_id = fpos.map_tax(self.product_id.supplier_taxes_id.filtered(lambda r: r.company_id.id == company_id))
		else:
			self.taxes_id = fpos.map_tax(self.product_id.supplier_taxes_id)

		if self.order_id.partner_id.is_foreign:
			self.taxes_id = None

		self._suggest_quantity()
		self._onchange_quantity()

		return result


PurchaseOrderLineInherit()