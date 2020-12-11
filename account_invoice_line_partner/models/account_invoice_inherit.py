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

import calendar

import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta
from odoo import api, models, fields, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import AccessError, UserError
import logging
_logger = logging.getLogger(__name__)

class AccountInvoiceInherit(models.Model):
	
	_inherit = 'account.invoice'

	@api.model
	def invoice_line_move_line_get(self):
		res = []
		for line in self.invoice_line_ids:
			if not line.account_id:
				continue
			if line.quantity==0:
				continue
			tax_ids = []
			for tax in line.invoice_line_tax_ids:
				tax_ids.append((4, tax.id, None))
				for child in tax.children_tax_ids:
					if child.type_tax_use != 'none':
						tax_ids.append((4, child.id, None))
			analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids]

			move_line_dict = {
				'invl_id': line.id,
				'type': 'src',
				'name': line.name,
				'price_unit': line.price_unit,
				'quantity': line.quantity,
				'price': line.price_subtotal,
				'account_id': line.account_id.id,
				'product_id': line.product_id.id,
				'uom_id': line.uom_id.id,
				'account_analytic_id': line.account_analytic_id.id,
				'analytic_tag_ids': analytic_tag_ids,
				'tax_ids': tax_ids,
				'invoice_id': self.id,
				}

			#se agrega esta clave del partner para poder realizar la validacion en la asignacion de la linea del movimiento
			#Se valida que solamente sea factura de proveedor
			if self.type == 'in_invoice':
				move_line_dict['partner_id'] = line.partner_line_id.id if line.partner_line_id.id else line.invoice_id.partner_id.id
			
			res.append(move_line_dict)
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
