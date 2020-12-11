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
from odoo.tools import float_is_zero, float_compare

class AccountInvoiceInherit(models.Model):

	_inherit = 'account.invoice'

	taxes_collected_id = fields.Many2one('taxes.collected', string = "Pago Impuestos")

	@api.onchange('taxes_collected_id')
	def onchange_taxes_collect(self):
		if self.taxes_collected_id:
			if self.invoice_line_ids:
				for x in self.invoice_line_ids:
					if not x.taxes_collected_id:
						x.taxes_collected_id = self.taxes_collected_id.id
						x.price_unit = 0
						
			#if self.taxes_collected_id.account_id:
				#self.account_id = self.taxes_collected_id.account_id.id


	def change_account_invoice_taxes(sefl, vals):
		if self.taxes_collected_id:
			vals['account_id'] = vals['taxes_collected_id']


	def return_tax_to_payy(self):
		"""
			Funcion que permite retornar el valor del impuesto del producto seleccionado, permitiendo de esta manera calcularlo
			aun con el precio del producto en 0
		"""
		price_unit = 0
		total_taxes = 0
		for line in self:
			
			if line.invoice_line_ids:

				for x in line.invoice_line_ids:

					if x.taxes_collected_id:

						price_product = 0

						if line.pricelist_id:

							price_product = line.pricelist_id.price_get(x.product_id.id, x.quantity, None)
							for value in price_product:
								price_unit = price_product.get(value)
						else:
					
							price_unit = x.product_id.list_price
						
						#if x.taxes_collected_id.type_taxes == 'tax_client':
			
						if x.price_unit == 0:

							currency = x.invoice_id and x.invoice_id.currency_id or None
							total_taxes += x.invoice_line_tax_ids.compute_all(price_unit, currency, x.quantity, product=x.product_id, partner=line.partner_id)['taxes'][0]['amount']


		_logger.info('Esto es lo que vamos a facturar')
		_logger.info(total_taxes)
		return total_taxes

	@api.multi
	def action_invoice_open(self):
		self._compute_amount()
		res = super(AccountInvoiceInherit, self).action_invoice_open()
		return res
	@api.one
	@api.depends(
		'state', 'currency_id', 'invoice_line_ids.price_subtotal',
		'move_id.line_ids.amount_residual',
		'move_id.line_ids.currency_id')
	def _compute_residual(self):
		fp_company = self.env['account.fiscal.position'].search(
			[('id', '=', self.company_id.partner_id.property_account_position_id.id)])
		company_tax_ids = [base_tax.tax_id.id for base_tax in fp_company.tax_ids_invoice]
		total_taxess = 0
		if self.taxes_collected_id.type_taxes == 'tax_company':
			total_taxess = self.return_tax_to_payy()
		residual = 0.0
		residual_company_signed = 0.0
		sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
		for line in self.sudo().move_id.line_ids:
			if line.tax_line_id.id not in company_tax_ids:
				if line.account_id.internal_type in ('receivable', 'payable'):
					residual_company_signed += line.amount_residual
					if line.currency_id == self.currency_id:
						residual += line.amount_residual_currency if line.currency_id else line.amount_residual
					else:
						from_currency = (line.currency_id and line.currency_id.with_context(date=line.date)) or line.company_id.currency_id.with_context(date=line.date)
						residual += from_currency.compute(line.amount_residual, self.currency_id)
		self.residual_company_signed = (abs(residual_company_signed) * sign) + total_taxess
		self.residual_signed = (abs(residual) * sign) + total_taxess
		self.residual = (abs(residual)) + total_taxess
		digits_rounding_precision = self.currency_id.rounding
		if float_is_zero(self.residual, precision_rounding=digits_rounding_precision):
			self.reconciled = True
		else:
			self.reconciled = False

	@api.one
	@api.depends('invoice_line_ids.price_subtotal',  'tax_line_ids.amount', 'tax_line_ids.amount_rounding', 'currency_id', 'company_id', 'date_invoice', 'type')
	def _compute_amount(self):

		super(AccountInvoiceInherit, self)._compute_amount()
		round_curr = self.currency_id.round
	
		total_taxess = self.return_tax_to_payy()
		self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)  

		#self.amount_tax = sum(round_curr(line.amount_total) for line in self.tax_line_ids) 
		#self.amount_total = self.amount_untaxed + self.amount_tax - total_taxess
		self.amount_total = self.amount_untaxed + self.amount_tax
	
	
	@api.multi
	def get_taxes_values(self):
		tax_grouped = {}
		round_curr = self.currency_id.round
		for line in self.invoice_line_ids:
			if not line.account_id:
				continue
			total_taxess = self.return_tax_to_payy()

			if total_taxess > 0:
				price_unit = 0
				price_product = 0

				if self.pricelist_id:

					price_product = self.pricelist_id.price_get(line.product_id.id, line.quantity, None)
					for value in price_product:
						price_unit = price_product.get(value)
				else:
					price_unit = line.product_id.list_price
				taxes = line.invoice_line_tax_ids.compute_all(price_unit, self.currency_id, line.quantity, line.product_id, self.partner_id)['taxes']
				for tax in taxes:
					val = self._prepare_tax_line_vals(line, tax)
					key = self.env['account.tax'].browse(tax['id']).get_grouping_key(val)

					if key not in tax_grouped:
						tax_grouped[key] = val
						tax_grouped[key]['base'] = round_curr(val['base'])
					else:
						tax_grouped[key]['amount'] += val['amount']
						tax_grouped[key]['base'] += round_curr(val['base'])
			else:
				price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
				taxes = line.invoice_line_tax_ids.compute_all(price_unit, self.currency_id, line.quantity, line.product_id, self.partner_id)['taxes']
				for tax in taxes:
					val = self._prepare_tax_line_vals(line, tax)
					key = self.env['account.tax'].browse(tax['id']).get_grouping_key(val)

					if key not in tax_grouped:
						tax_grouped[key] = val
						tax_grouped[key]['base'] = round_curr(val['base'])
					else:
						tax_grouped[key]['amount'] += val['amount']
						tax_grouped[key]['base'] += round_curr(val['base'])
		return tax_grouped
		
	"""

	@api.onchange('invoice_line_ids')
	def _onchange_invoice_line_ids(self):
		taxes_grouped = self.get_taxes_values()
		_logger.info('Hola impuesto')
		_logger.info(taxes_grouped)
		tax_lines = self.tax_line_ids.filtered('manual')
		for tax in taxes_grouped.values():
			tax_lines += tax_lines.new(tax)
		self.tax_line_ids = tax_lines
		return True

	"""

	@api.model
	def create(self, vals):

		if 'origin' in vals:

			sale_order = self.env['sale.order'].search([('name', '=', vals['origin'])], limit=1)
			if sale_order.order_line:
				print('entramos')
				product_data= []
				vals['pricelist_id'] = sale_order.pricelist_id.id

				if sale_order.taxes_collected_id:
					vals['taxes_collected_id'] = sale_order.taxes_collected_id.id

					self.onchange_taxes_collect()

					for x in sale_order.order_line:
						#if x.taxes_collected_id.type_taxes == 'tax_client':
						product_data.append(x.product_id.id)

					if product_data:
						if 'invoice_line_ids' in vals:

							for x in vals['invoice_line_ids']:
								if x.product_id.id in product_data:
									x.write({'taxes_collected_id': sale_order.taxes_collected_id.id})

					self._compute_amount()
					#self.change_account_invoice_taxes(vals)
		
		res = super(AccountInvoiceInherit, self).create(vals)

		return res


	@api.multi
	def write(self, vals):

		#self.change_account_invoice_taxes(vals)
		
		res = super(AccountInvoiceInherit, self).write(vals)

		return res


	@api.multi
	def action_move_create(self):
		""" Creates invoice related analytics and financial move lines """
		account_move = self.env['account.move']

		for inv in self:
			if not inv.journal_id.sequence_id:
				raise UserError(_('Please define sequence on the journal related to this invoice.'))
			if not inv.invoice_line_ids.filtered(lambda line: line.account_id):
				raise UserError(_('Please add at least one invoice line.'))
			if inv.move_id:
				continue


			if not inv.date_invoice:
				inv.write({'date_invoice': fields.Date.context_today(self)})
			if not inv.date_due:
				inv.write({'date_due': inv.date_invoice})
			company_currency = inv.company_id.currency_id

			# create move lines (one per invoice line + eventual taxes and analytic lines)
			iml = inv.invoice_line_move_line_get()
			iml += inv.tax_line_move_line_get()

			diff_currency = inv.currency_id != company_currency
			# create one move line for the total and possibly adjust the other lines amount
			total, total_currency, iml = inv.compute_invoice_totals(company_currency, iml)

			name = inv.name or ''
			if inv.payment_term_id:
				totlines = inv.payment_term_id.with_context(currency_id=company_currency.id).compute(total, inv.date_invoice)[0]
				res_amount_currency = total_currency
				for i, t in enumerate(totlines):
					if inv.currency_id != company_currency:
						amount_currency = company_currency._convert(t[1], inv.currency_id, inv.company_id, inv._get_currency_rate_date() or fields.Date.today())
					else:
						amount_currency = False

					# last line: add the diff
					res_amount_currency -= amount_currency or 0
					if i + 1 == len(totlines):
						amount_currency += res_amount_currency

					_logger.info(inv)
					iml.append({
						'type': 'dest',
						'name': name,
						'price': t[1],
						'account_id': inv.account_id.id,
						'date_maturity': t[0],
						'amount_currency': diff_currency and amount_currency,
						'currency_id': diff_currency and inv.currency_id.id,
						'invoice_id': inv.id,
						#'partner_id': inv.partner_line_id.id
					})
			else:
				_logger.info(inv)
				total_taxes_to_pay = self.return_tax_to_payy()

				if inv.taxes_collected_id.type_taxes == 'tax_company':
					iml.append({
					'type': 'dest',
					'name': name,
					'price': total_taxes_to_pay,
					'account_id': inv.taxes_collected_id.account_id.id,
					'date_maturity': inv.date_due,
					'amount_currency': diff_currency and total_currency,
					'currency_id': diff_currency and inv.currency_id.id,
					'invoice_id': inv.id,
					#'partner_id': inv.partner_line_id.id
					})
					iml.append({
					'type': 'dest',
					'name': name,
					'price': total- total_taxes_to_pay,
					'account_id': inv.account_id.id,
					'date_maturity': inv.date_due,
					'amount_currency': diff_currency and total_currency,
					'currency_id': diff_currency and inv.currency_id.id,
					'invoice_id': inv.id,
					#'partner_id': inv.partner_line_id.id
					})

				else:
					iml.append({
					'type': 'dest',
					'name': name,
					'price': total,
					'account_id': inv.account_id.id,
					'date_maturity': inv.date_due,
					'amount_currency': diff_currency and total_currency,
					'currency_id': diff_currency and inv.currency_id.id,
					'invoice_id': inv.id,
					#'partner_id': inv.partner_line_id.id
				})

			part = self.env['res.partner']._find_accounting_partner(inv.partner_id)

			#validamo que sea una factura de proveedor
			if self.type == 'in_invoice':
				data_new = []
				for l in iml:
					if 'partner_id' in l:
						if l['partner_id']:
							data_new.append((0, 0, self.line_get_convert(l, l['partner_id'])) )
					else:
						data_new.append((0, 0, self.line_get_convert(l, part.id)) )

				line = [l for l in data_new ]
			else:
				line = [(0, 0, self.line_get_convert(l, part.id)) for l in iml ]

			line = inv.group_lines(iml, line)

			line = inv.finalize_invoice_move_lines(line)

			date = inv.date or inv.date_invoice
			move_vals = {
				'ref': inv.reference,
				'line_ids': line,
				'journal_id': inv.journal_id.id,
				'date': date,
				'narration': inv.comment,
			}

			move = account_move.create(move_vals)
			# Pass invoice in method post: used if you want to get the same
			# account move reference when creating the same invoice after a cancelled one:
			move.post(invoice = inv)
			# make the invoice point to that move
			vals = {
				'move_id': move.id,
				'date': date,
				'move_name': move.name,
			}
			inv.write(vals)
		return True


AccountInvoiceInherit()