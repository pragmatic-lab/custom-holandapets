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

MAP_INVOICE_TYPE_PARTNER_TYPE = {
	'out_invoice': 'customer',
	'out_refund': 'customer',
	'in_invoice': 'supplier',
	'in_refund': 'supplier',
}


class AccountInvoicePaymentActionConfirm(models.Model):

	_name = 'account.invoice_payment_action_confirm'
	_rec_name= 'invoice_id'


	def _default_invoice(self):
		default_invoice = self._context.get('ctx_invoice_id')

		return default_invoice

	invoice_id = fields.Many2one('account.invoice', string="Factura", default=_default_invoice, readonly=True, store=True)
	payment_action_ids = fields.One2many('account.invoice_payment_action', 'invoice_payment_id', string="Pagos")

	@api.multi
	def button_payment_invoice_complete(self):

		"""
			Funcion que permite hacer multiples pagos por factura, estos pagos son los que se encuentran
			en la relacion payment_action_ids, una vez pulsen el boton validar, realizará el respectivo
			pago
		"""
		invoice_id = self._context.get('ctx_invoice_id')


		invoice = self.env['account.invoice'].search([('id', '=', invoice_id)])

		data= []
		model_account_abstract_payment = self.env['account.abstract.payment']


		total_amount = model_account_abstract_payment._compute_payment_amount(invoices=invoice, currency=invoice.currency_id)
		if self.payment_action_ids:

			for x in self.payment_action_ids:

				payment_type = total_amount > 0 and 'inbound' or 'outbound'

				if x.amount_total > 0:

					vals = {

						'payment_type': total_amount > 0 and 'inbound' or 'outbound', 
						'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoice[0].type] or False,
						'partner_id': invoice.partner_id.id,
						'amount': x.amount_total - x.money_back,
						'currency_id': invoice.currency_id.id,
						'payment_date': str(datetime.today())[0:10],
						'journal_id': x.journal_id.id,
						'communication': ' '.join([ref for ref in invoice.mapped('reference') if ref])[:2000],
						'payment_difference_handling': 'open',
						'writeoff_label': 'Write-Off',
						'payment_method_id': 1 if payment_type == 'inbound' else 2,
						'payment_token_id': False, 
						'partner_bank_account_id': False, 
						'writeoff_account_id': False,
						'invoice_ids': [(4, invoice.id, None)],
						'number_authorization': x.payment_ref or ''
					}


					model_payment = self.env['account.payment'].create(vals)
					model_payment.action_validate_invoice_payment()

					
AccountInvoicePaymentActionConfirm()