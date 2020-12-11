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

class AccountInvoicePaymentActionConfirm(models.Model):

	_name = 'account.invoice_payment_action'

	invoice_id = fields.Many2one('account.invoice', string="Account Invoice")
	
	invoice_payment_id = fields.Many2one('account.invoice_payment_action_confirm', string="Account Invoice Payment")
	journal_id = fields.Many2one('account.journal', string=u"Método de Pago", required=True, domain="[('type', 'in', ['cash', 'bank'])]")
	amount_total = fields.Float(string="Pago")
	amount_target = fields.Float(string="Monto")
	payment_ref = fields.Char(string="Autorizacion")
	amount_iva = fields.Float(string="Iva")
	money_back = fields.Float(string="Devuelta")



	def return_amount_total_current(self):
		"""
			Funcion que retorna el valor pagado que lleva hasta el momento
		"""
		invoice_id = self._context.get('ctx_invoice_id')
		invoice = self.env['account.invoice'].search([('id', '=', invoice_id)])

		amount_total = 0

		for x in self:
			if x.invoice_payment_id.payment_action_ids:
				payment_action_ids = x.invoice_payment_id.payment_action_ids
				if payment_action_ids:
					for payment in payment_action_ids:
						amount_total += payment.amount_total

		if amount_total == 0:
			amount_total = invoice.amount_total - invoice.residual

		return amount_total

	@api.depends('journal_id')
	@api.onchange('journal_id')
	def onchange_calculate_amount_total(self):
		"""
			Funcion que permite calcular:
			-> Valor a pagar
			-> Monto para el datafono
			-> Iva para el datafono
		"""

		invoice_id = self._context.get('ctx_invoice_id')


		invoice = self.env['account.invoice'].search([('id', '=', invoice_id)])

		for x in self:
			if x.journal_id:
				amount_total = self.return_amount_total_current()

				if amount_total > 0:
					if amount_total != invoice.amount_total:
						_logger.info(amount_total)
						_logger.info(invoice.amount_total)
						x.amount_total = invoice.amount_total - amount_total
				else:
					x.amount_total = invoice.amount_total


				if x.amount_total:

					#impuestos
					total = invoice.amount_total
					amount_taxes = invoice.amount_tax
					amount_read = x.amount_total 

					
					amount_iva = (amount_read * amount_taxes)/total
					amount_target = amount_read - amount_iva

					x.amount_iva = amount_iva
					x.amount_target = amount_target 

	@api.depends('amount_total')
	@api.onchange('amount_total')
	def onchange_calculate_payment_taxes(self):
		"""
			Funcion que permite calcular:
			-> Monto para el datafono
			-> Iva para el datafono
			-> Devuelta
		"""
		invoice_id = self._context.get('ctx_invoice_id')

		invoice = self.env['account.invoice'].search([('id', '=', invoice_id)])

		for x in self:
			if x.amount_total > 0:

				#impuestos
				total = invoice.amount_total
				amount_taxes = invoice.amount_tax
				amount_read = x.amount_total 

				
				amount_iva = (amount_read * amount_taxes)/total
				amount_target = amount_read - amount_iva

				x.amount_iva = amount_iva
				x.amount_target = amount_target

			value_current_amount = self.return_amount_total_current() - x.amount_total
			if value_current_amount > invoice.amount_total:
				x.money_back = value_current_amount - invoice.amount_total
			else:
				x.money_back = 0


AccountInvoicePaymentActionConfirm()