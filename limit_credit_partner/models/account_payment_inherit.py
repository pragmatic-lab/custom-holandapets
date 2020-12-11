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
from odoo.addons import decimal_precision as dp

class AccountPaymentInherit(models.Model):

	_inherit = "account.payment"


	def update_credit_limit(self, payment_id, amount_total):
		if self.partner_id:
			if self.amount > 0:
				_logger.info('entramos para realizar pago')
				model_credit_limit = self.env['limit.credit_partner']

				_logger.info('el partner para el pago es:')
				_logger.info(self.partner_id.name)
				model_credit_limit.update_credit_limit_partner(self.partner_id.id, amount_total, 1, payment_id, None)


	@api.multi
	def post(self):

		super(AccountPaymentInherit, self).post()

		_logger.info('confirmando pago')

		if self.partner_id and self.amount > 0:


			self.update_credit_limit(self.id, self.amount)


AccountPaymentInherit()