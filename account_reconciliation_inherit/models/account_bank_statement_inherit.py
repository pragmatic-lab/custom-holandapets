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
import json 
import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta
from odoo import api, models, fields, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import AccessError, UserError
import logging
_logger = logging.getLogger(__name__)
import json
from ast import literal_eval

class AccountBankStatement(models.Model):
	_inherit = 'account.bank.statement'

	@api.multi
	def action_bank_reconcile_bank_statements_inherit(self):
		print(self)
		print(self.env.context)

		context = self.env.context.copy()
		context.update( { 'hide_record': True, 'account_bs':self.id, 'date_to_validate': self.date } ) 
		self.env.context = context

		action = self.env.ref('account.action_bank_reconcile_bank_statements').read()[0]
		action.update({
			'context':  action['context'][:len(action['context'])-1] + ", 'hide_record': True, 'account_bs':" + str(self.id) + ", 'date_to_validate':" + str(self.date) + " }",
		})
		print(self.env.context)

		return action

AccountBankStatement()