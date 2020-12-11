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
from odoo.exceptions import UserError, ValidationError
class SaleOrderInherit(models.Model):

	_inherit = 'sale.order'

	taxes_collected_id = fields.Many2one('taxes.collected', string = "Pago Impuestos")


	@api.onchange('order_line')
	def onchange_order_line_taxes_collected(self):
		record_id = None
		if self.order_line:
			for x in self.order_line:
				if not x.taxes_collected_id:
					if x.price_unit == 0:
						x.product_id_change()
				if x.taxes_collected_id:
					if record_id == None:
						record_id = x.taxes_collected_id.id
						self.taxes_collected_id = x.taxes_collected_id.id
					else:
						if record_id != x.taxes_collected_id.id:
							raise ValidationError(_('Solmente puede seleccionar un mismo tipo de pago impuesto. \n Si desea aplicar uno diferente al anteriormente establecido deberá realizar una nueva cotización. \n Si cree que esto es un error comuniquese con el Administrador ') )
						

	def contain_customer_taxes(self):
		"""
			Funcion que permite validar si en las lines hay configurado un impuestos para cliente o proveedor
		"""
		if self.order_line:
			for x in self.order_line:
				if x.taxes_collected_id:
					return True
		return False


	# @api.onchange('taxes_collected_id')
	# def onchange_taxes_collect(self):
	# 	if self.taxes_collected_id:
	# 		if self.order_line:
	# 			for x in self.order_line:
	# 				if not x.taxes_collected_id:
	# 					x.taxes_collected_id = self.taxes_collected_id.id
	# 					x.price_unit = 0


	def return_price_to_pay(self):
		"""
			Funcion que permite retornar el valor del impuesto del producto seleccionado, permitiendo de esta manera calcularlo
			aun con el precio del producto en 0
			A cargo del cliente: Se muestra el IVA solamente y el impuesto en la contabilizacion va hacian la cuenta 130501
			A cargo de la Empresa: Se muestra el IVA y en la contabilización se tiene que cambiar a la cuenta que se configuro
		"""

		price_tax = 0
		for x in self:
			
			if x.order_line:

				for line in x.order_line:


					if line.product_id:

						if x.pricelist_id:

							if line.taxes_collected_id:

								price_product = x.pricelist_id.price_get(line.product_id.id, line.product_uom_qty, None) or 0
								price_unit = 0

								for value in price_product:
									price_unit = price_product.get(value)

								print(price_unit)

								if line.price_unit == 0:

									taxes = line.tax_id.compute_all(price_unit, x.currency_id, line.product_uom_qty, product=line.product_id, partner=x.partner_shipping_id)
									price_tax = sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])) 


		_logger.info('Esto es lo que vamos a facturar')
		_logger.info('el precio es: {}'.format(price_tax))
		return price_tax



	@api.depends('order_line.price_total', 'order_line.taxes_collected_id', 'order_line.price_subtotal', 'amount_untaxed', 'amount_total', 'order_line.product_uom_qty')
	def _amount_all(self):
		"""
		Compute the total amounts of the SO.
		"""
		super(SaleOrderInherit, self)._amount_all()
		total_taxes = self.return_price_to_pay() or 0
		print('entrando en el calculo por aca')
		print(total_taxes)
		# for order in self:
		# 	amount_untaxed = amount_tax = 0.0
		# 	for line in order.order_line:
		# 		amount_untaxed += line.price_subtotal
		# 		amount_tax += line.price_tax
		# 	print('la suma total es {}'.format(amount_untaxed + total_taxes))
		# 	order.amount_tax  = amount_untaxed + total_taxes
		# 	order.amount_total = amount_untaxed + amount_tax
		# 	order.update({
		# 		'amount_untaxed': amount_untaxed + total_taxes,
		# 		'amount_total': amount_untaxed + amount_tax,
		# 	})
		flag = False
		for order in self:
			amount_untaxed = amount_tax = 0.0
			for line in order.order_line:
				amount_untaxed += line.price_subtotal
				amount_tax += line.price_tax
				if line.taxes_collected_id:
					flag= True
			if not flag:
				total_taxes = 0
			order.update({
				'amount_untaxed': amount_untaxed,
				'amount_tax': amount_tax+ total_taxes,
				'amount_total': amount_untaxed + amount_tax + total_taxes,
			})

	@api.multi
	def _prepare_invoice(self):
		"""
		Prepare the dict of values to create the new invoice for a sales order. This method may be
		overridden to implement custom invoice generation (making sure to call super() to establish
		a clean extension chain).
		"""
		self.ensure_one()
		journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
		if not journal_id:
			raise UserError(_('Please define an accounting sales journal for this company.'))
		invoice_vals = {
			'name': self.client_order_ref or '',
			'origin': self.name,
			'type': 'out_invoice',
			'account_id': (self.partner_invoice_id.property_account_receivable_id.id),
			'partner_id': self.partner_invoice_id.id,
			'partner_shipping_id': self.partner_shipping_id.id,
			'journal_id': journal_id,
			'currency_id': self.pricelist_id.currency_id.id,
			'comment': self.note,
			'payment_term_id': self.payment_term_id.id,
			'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
			'company_id': self.company_id.id,
			'user_id': self.user_id and self.user_id.id,
			'team_id': self.team_id.id,
			'transaction_ids': [(6, 0, self.transaction_ids.ids)],
		}

		return invoice_vals

SaleOrderInherit()