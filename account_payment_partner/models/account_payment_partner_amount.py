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

class AccountPaymentPartnerAmount(models.Model):
	
	_name = 'account.payment_partner_amount'
	_rec_name = 'amount'
	_order = 'account_ml_id asc'


	def return_amount(self, account_ml_id):
		amount = 0

		type_partner = account_ml_id.partner_id.supplier
		
		if type_partner == False:
			amount = account_ml_id.credit
		else:
			amount = account_ml_id.debit
		return amount

	@api.multi
	def name_get(self):
		result = []
		for record in self:
			amount = self.return_amount(record.account_ml_id)
			result.append((record.id, "%s" % (amount)))
		return result



	def _compute_amount_payment(self):
		"""
			Funcion que permite cargar:
				-> Amount

		"""
		for x in self:
	
			x.amount = self.return_amount(x.account_ml_id)
			x.partner_id = x.account_ml_id.partner_id.id

	account_ml_id = fields.Many2one('account.move.line', string="Account Move Line")
	partner_id = fields.Many2one(related='account_ml_id.partner_id', string=u"Tercero")
	amount = fields.Float(string=u"Total", compute='_compute_amount_payment')


AccountPaymentPartnerAmount()