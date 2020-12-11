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

from odoo import api, fields, models

import pprint
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _
from odoo.tools import float_is_zero, float_compare
from odoo.tools.misc import formatLang
from datetime import datetime

import pprint
import logging
_logger = logging.getLogger(__name__)

class SaleOrderInherit(models.Model):
	_inherit = 'sale.order'

	@api.depends('partner_id')
	def compute_active_day_iva(self):
		for x in self:
			x.active_day_iva = x.return_validate_day_iva()

	@api.depends('partner_id')
	def compute_amount_day_iva(self):
		for x in self:
			amount_day_iva = x.return_amount_day_iva()
			x.html_active_amount_day = """
				<div class="alert alert-success">
					<h4 class="alert-heading">Día sin IVA!</h4>
					<hr>
					<p>Querido usuario, tenga presente que el valor máximo permitido sin IVA el de hoy sera de <strong> $%s</strong>. Tenga presente que solamente los productos van a estar exentos de IVA, si se cacenla con <strong>Tarjeta</strong></p>
				</div>
			"""%(amount_day_iva)


	TYPE_PAYMENT = [ ('cash', 'Efectivo'),
						('bank', 'Tarjetas')]
	wh_taxes = fields.Float(string="Retenciones", store=True, compute="amount_wh_taxes")
	taxes_ids = fields.One2many('sale.order.tax', 'order_id', string='Impuestos', compute='_compute_sale_order_taxes', store=True)
	type_payment = fields.Selection(TYPE_PAYMENT, string="Tipo de Pago")
	active_day_iva = fields.Boolean(string="Active Day Iva", compute='compute_active_day_iva')
	html_active_amount_day = fields.Html(string="Amount Day Iva", compute='compute_amount_day_iva')


	def return_validate_day_iva(self):
		#active_day = self.env.sudo().ref('l10n_co_tax_extension.ir_config_active_day_without_iva')
		active_day = self.env['ir.config_parameter'].sudo().search([('key', '=', 'active.day.iva')])
		
		flag = False
		if active_day:
			if active_day.value == '1':
				flag= True
		return flag
		
	def return_amount_day_iva(self):
		amount_day_iva = self.env['ir.config_parameter'].sudo().search([('key', '=', 'base.amount.day.iva')])
		#amount_day_iva = self.env.sudo().ref('l10n_co_tax_extension.ir_config_amount_day_without_iva')
		if amount_day_iva:
			return float(amount_day_iva.value)
		return 0

	@api.model
	def default_get(self, default_fields):
		amount_day_iva = self.return_amount_day_iva()
		res= super(SaleOrderInherit, self).default_get(default_fields)

		res['active_day_iva'] = self.return_validate_day_iva()
		res['html_active_amount_day'] = """
				<div class="alert alert-success">
					<h4 class="alert-heading">Día sin IVA!</h4>
					<hr>
					<p>Querido usuario, tenga presente que el valor máximo permitido sin IVA el de hoy sera de <strong> $%s</strong>. Tenga presente que solamente los productos van a estar exentos de IVA, si se cacenla con <strong>Tarjeta</strong></p>
				</div>


			"""%(amount_day_iva)

		return res





	@api.onchange('order_line')
	def onchange_order_line_validate_day_iva(self):


		if self.return_validate_day_iva():

			amount_untaxed = 0.0
			for line in self.order_line:
				amount_untaxed += line.price_subtotal
			amount_total = amount_untaxed
			amount_day_iva = self.return_amount_day_iva()

			if amount_day_iva > 0:
				if amount_total > amount_day_iva:
					print('si es')
					for x in self.order_line:
						x.product_id_change()
						x.onchange_calculate_tax()




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

							flag=self.validate_type(x.tax_id, 'sale', date)

							if flag:
								data.append(x.tax_id.id)

		#data contiene las retenciones que fueron establecidas en la posicion fiscal
		return data


	@api.one
	@api.depends('order_line.price_total', 'amount_tax', 'wh_taxes')
	def amount_wh_taxes(self):
		"""
		Compute the total amounts of the SO.
		"""

		for order in self:
			data_wh_taxes = order.return_data_wh_taxes()
			
			#suma total de impuestos
			sum_amount_total = sum(line.amount for line in order.taxes_ids if line.tax_id.id not in data_wh_taxes)
			
			#suma de retenciones
			sum_wh_taxes = 0

			if order.fiscal_position_id:
				#suma de retenciones
				if data_wh_taxes:
					sum_wh_taxes = sum(line.amount for line in order.taxes_ids if line.tax_id.id in data_wh_taxes)

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


	@api.depends('order_line.price_total')
	def _amount_all(self):
		"""
		Compute the total amounts of the SO.
		"""
		super(SaleOrderInherit, self)._amount_all()

		for order in self:
			data_wh_taxes = order.return_data_wh_taxes()
			#suma total de impuestos
			sum_amount_total = sum(line.amount for line in order.taxes_ids if line.tax_id.id not in data_wh_taxes)
				
			amount_untaxed = amount_tax = 0.0
			for line in order.order_line:
				amount_untaxed += line.price_subtotal
				amount_tax += line.price_tax

			order.update({
				'amount_untaxed': amount_untaxed,
				'amount_tax': sum_amount_total,
				'amount_total': amount_untaxed + amount_tax,
			})


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
						'tax_id': tax['id'],
						'name': tax['name'],
						'amount': tax['amount'],
						'base': currency.round(tax['base']),
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
				#_logger.info('jhhjfdshjdfshfdshkfdshkfjsd')
				#_logger.info(tax)	
				if tax['tax_id']:		
					vals = {
						'sequence': tax['sequence'],
						'tax_id': tax['tax_id'],
						'name': tax['name'],
						'base': tax['base'],
						'amount': tax['amount']}
					data.append((0, 0, vals))

		self.taxes_ids = data
	@api.multi
	def _prepare_invoice(self):
		invoice_vals = super(SaleOrderInherit, self)._prepare_invoice()
		invoice_vals['date_invoice'] = fields.Date.context_today(self)
		return invoice_vals

	@api.multi
	def update_records_lines(self):

		order_ids = self.env['sale.order'].search([('state', '=', 'draft')])

		if order_ids:
			for x in order_ids:

				if x.order_line:

					for line in x.order_line:
						line.product_id_change()
						

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
						flag = self.validate_type(x.tax_id, 'sale', date)

						if flag:
							data.append(x.tax_id.id)

		if product_id:
			#validamos que impuestos tienen los productos predefinidos
			fpos = self.fiscal_position_id or self.partner_id.property_account_position_id
			# If company_id is set, always filter taxes by the company
			taxes = product_id.taxes_id.filtered(lambda r: not self.company_id or r.company_id == self.company_id)
			taxes_ids = fpos.map_tax(taxes, product_id, self.partner_shipping_id) if fpos else taxes
			print(taxes_ids)

			if product_id.without_retention:

				data_product = []

				if taxes_ids:
					for x in taxes_ids:
						data_product.append(x.id)

				return data_product

			else:

				if taxes_ids:
					
					if self.type_payment == 'cash':
						for x in taxes_ids:
							print(x.inactive_tax)
							data.append(x.id)

					else:

						amount_untaxed = 0.0
						for line in self.order_line:
							amount_untaxed += line.price_subtotal
						amount_total = amount_untaxed
						amount_day_iva = self.return_amount_day_iva()

						print(amount_total)
						print(amount_day_iva)
						if amount_day_iva > 0:

							if amount_total > amount_day_iva:

								for x in taxes_ids:
									data.append(x.id)

							else:
								for x in taxes_ids:
									if x.inactive_tax == False:
										data.append(x.id)

						else:
							for x in taxes_ids:
								if x.inactive_tax == False:
									data.append(x.id)

			return data

	@api.multi
	@api.onchange('order_line')
	def update_records_order_create_write(self):
		if self.order_line:
			for x in self.order_line:
				if x.product_id:
					x.tax_id = [(6, _, self.update_taxes(x.product_id))]
					#x.write({'tax_id': [(6, _, self.update_taxes(x.product_id))]})

	@api.multi
	def update_records_order_line(self):
		self.update_records_order_create_write()
		self._compute_sale_order_taxes()


SaleOrderInherit()


class SaleOrderLineInherit(models.Model):

	_inherit = 'sale.order.line'

	@api.onchange('price_unit', 'product_uom_qty', 'product_id')
	def onchange_calculate_tax(self):
		"""
			Funcion que permite cargar los impuestos configurados en la posicion fiscal
		"""

		if self.product_id:
			data = self.order_id.update_taxes(self.product_id)

			fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
			# If company_id is set, always filter taxes by the company
			taxes = self.product_id.taxes_id.filtered(lambda r: not self.company_id or r.company_id == self.company_id)
			taxes_ids = fpos.map_tax(taxes, self.product_id, self.order_id.partner_shipping_id) if fpos else taxes

			total_taxes = 0

			if taxes_ids:
				for x in taxes_ids:
					print(x.name)
					print(x.amount)
					total_taxes += self.price_unit * ( (x.amount)/100 )

			#print('precio unitario ' + str(self.price_unit))
			#print('total taxes: ' + str(total_taxes))
			#self.tax_id = [(6, _, data)]

			#self.price_unit = taxes['total_excluded']


	@api.multi
	@api.onchange('product_id')
	def product_id_change(self):

		res = super(SaleOrderLineInherit, self).product_id_change()

		if self.order_id.return_validate_day_iva():

			print('estamos entrando')
			if self.order_id.amount_untaxed < self.order_id.return_amount_day_iva():

				price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
				taxes = self.tax_id.compute_all(price, self.order_id.currency_id, self.product_uom_qty, product=self.product_id, partner=self.order_id.partner_shipping_id)
	
				self.price_unit = taxes['total_excluded']

		return res


SaleOrderLineInherit()