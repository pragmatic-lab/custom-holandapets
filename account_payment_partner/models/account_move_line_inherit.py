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
from odoo.exceptions import UserError
from collections import OrderedDict
import json
import re
import uuid
from functools import partial

from lxml import etree
from dateutil.relativedelta import relativedelta
from werkzeug.urls import url_encode

from odoo import api, exceptions, fields, models, _
from odoo.tools import email_re, email_split, email_escape_char, float_is_zero, float_compare, \
	pycompat, date_utils
from odoo.tools.misc import formatLang

from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning

from odoo.addons import decimal_precision as dp
import logging
import logging
_logger = logging.getLogger(__name__)

class AccountMoveLineInherit(models.Model):
	_inherit = "account.move.line"

	@api.model
	def update_amount_reconcile(self, temp_amount_residual, temp_amount_residual_currency, amount_reconcile, credit_move, debit_move):

		super(AccountMoveLineInherit, self).update_amount_reconcile(temp_amount_residual, temp_amount_residual_currency, amount_reconcile, credit_move, debit_move)
		# Check if amount is positive
		paid_amt = self.env.context.get('paid_amount', 0.0)
		if not paid_amt:
			return temp_amount_residual, temp_amount_residual_currency, \
				amount_reconcile
		paid_amt = float(paid_amt)
		if paid_amt < 0:
			raise UserError(_("The specified amount has to be strictly positive"))

		# We need those temporary value otherwise the computation might
		# be wrong below

		# Compute paid_amount currency
		if debit_move.amount_residual_currency or \
				credit_move.amount_residual_currency:

			temp_amount_residual_currency = min(
				debit_move.amount_residual_currency,
				-credit_move.amount_residual_currency,
				paid_amt)
		else:
			temp_amount_residual_currency = 0.0

		# If previous value is not 0 we compute paid amount in the company
		# currency taking into account the rate
		if temp_amount_residual_currency:
			paid_amt = debit_move.currency_id._convert(
				paid_amt, debit_move.company_id.currency_id,
				debit_move.company_id,
				credit_move.date or fields.Date.today())
		temp_amount_residual = min(debit_move.amount_residual,
								   -credit_move.amount_residual,
								   paid_amt)
		amount_reconcile = temp_amount_residual_currency or \
			temp_amount_residual

		return temp_amount_residual, temp_amount_residual_currency, \
			amount_reconcile

	@api.model
	def _check_remove_debit_move(self, amount_reconcile, debit_move, field):
		res = super(AccountMoveLineInherit, self)._check_remove_debit_move(amount_reconcile, debit_move, field)
		if not isinstance(self.env.context.get('paid_amount', False), bool):
			return True
		return res

	@api.model
	def _check_remove_credit_move(self, amount_reconcile, credit_move, field):
		res = super(AccountMoveLineInherit, self)._check_remove_credit_move(amount_reconcile, credit_move, field)
		if not isinstance(self.env.context.get('paid_amount', False), bool):
			return True
		return res

	@api.model
	def return_reconcile_data_ids(self):

		ids = []
		for aml in self:
			if aml.account_id.reconcile:
				ids.extend([r.debit_move_id.id for r in aml.matched_debit_ids] if aml.credit > 0 else [r.credit_move_id.id for r in aml.matched_credit_ids])
				ids.append(aml.id)

		return ids

AccountMoveLineInherit()