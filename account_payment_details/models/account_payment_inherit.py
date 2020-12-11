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

from num2words import num2words
from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)


class AccountPaymentInherit(models.Model):
	_inherit = "account.payment"
	
	text_amount = fields.Char(string="Valor en letras", required=False, compute="amount_to_words" )

	
	def amount_to_words(self):
		if self.company_id.text_amount_language_currency:
			self.text_amount = str(num2words(self.amount, to='currency', lang=self.company_id.text_amount_language_currency)).upper()	

	@api.depends('amount')
	def load_records_move_lines(self):

		move_line_ids = self.env['account.move.line'].search([('payment_id', 'in', self.ids)])
		_logger.info('los movimientos son')
		_logger.info(move_line_ids)
		for x in move_line_ids:
			_logger.info(x.debit)
		return move_line_ids
AccountPaymentInherit()