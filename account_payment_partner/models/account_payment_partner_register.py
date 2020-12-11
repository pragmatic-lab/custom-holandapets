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
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import logging
_logger = logging.getLogger(__name__)

class AccountPaymentPartnerRegister(models.Model):
	
	_name = 'account.payment_partner_register'
	_rec_name = 'invoice_id'
	_order = 'invoice_id desc'



	def _compute_amount_payment(self):
		"""
			Funcion que permite cargar:
				-> Valor de la factura
				-> Total pagado
				-> Total adeudado
		"""
		for x in self:
			invoice = x.invoice_id
			x.amount_payment = invoice.amount_total - invoice.residual
			x.residual = invoice.residual
			x.amount_total = invoice.amount_total
			x.partner_id = invoice.partner_id.id

	account_payment_id = fields.Many2one('account.payment', string="Pago")
	register_payment_id = fields.Many2one('account.payment', string="Pago Valido")
	account_entries_payment_id = fields.Many2one('account.entries_payment_partner', string="Pago")
	register_entries_payment_id = fields.Many2one('account.entries_payment_partner', string="Pago Valido")
	invoice_id = fields.Many2one('account.invoice', string="Factura")
	partner_id = fields.Many2one(related='invoice_id.partner_id', string=u"Tercero")
	amount_total = fields.Float(string=u"Total", compute='_compute_amount_payment')
	residual = fields.Float(string=u"Residuo", compute='_compute_amount_payment')
	amount_payment = fields.Float(string=u"Total Pagado", compute='_compute_amount_payment')
	amount = fields.Float(string="Pagar", required=True, default=0)
	state = fields.Boolean(string="Pagado", readonly=True, store=True, default=False)
	acount_ml_amount_id = fields.Many2one('account.payment_partner_amount', string="Pago", domain="[('partner_id', '=', partner_id)]")

	@api.depends('amount')
	@api.onchange('amount')
	def onchange_amount(self):
		for x in self:
			if x.residual > 0:
				if x.amount > x.residual:
					raise Warning(_(u'No puede pagar más del valor adeudado. \n Si cree que esto es un error. Por favor comuniquese con el Administrador'))

	@api.depends('acount_ml_amount_id')
	@api.onchange('acount_ml_amount_id')
	def onchange_acount_ml_amount_id(self):
		for x in self:
			if x.acount_ml_amount_id:
				x.amount = x.acount_ml_amount_id.amount


AccountPaymentPartnerRegister()