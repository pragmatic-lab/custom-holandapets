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

class AccountInvoiceInherit(models.Model):

	_inherit = 'account.invoice'

	@api.one
	def get_credit_payments_current(self):
		
		if self.state == 'open':
			domain = [('account_id', '=', self.account_id.id),
					  ('partner_id', '=', self.env['res.partner']._find_accounting_partner(self.partner_id).id),
					  ('reconciled', '=', False),
					  '|',
						'&', ('amount_residual_currency', '!=', 0.0), ('currency_id','!=', None),
						'&', ('amount_residual_currency', '=', 0.0), '&', ('currency_id','=', None), ('amount_residual', '!=', 0.0)]
			if self.type in ('out_invoice', 'in_refund'):
				domain.extend([('credit', '>', 0), ('debit', '=', 0)])
				type_payment = _('Outstanding credits')
			else:
				domain.extend([('credit', '=', 0), ('debit', '>', 0)])
				type_payment = _('Outstanding debits')
			info = {'title': '', 'outstanding': True, 'content': [], 'invoice_id': self.id}
			lines = self.env['account.move.line'].search(domain)
			currency_id = self.currency_id
			if len(lines) != 0:
				for line in lines:
					# get the outstanding residual value in invoice currency
					if line.currency_id and line.currency_id == self.currency_id:
						amount_to_show = abs(line.amount_residual_currency)
					else:
						currency = line.company_id.currency_id
						amount_to_show = currency._convert(abs(line.amount_residual), self.currency_id, self.company_id, line.date or fields.Date.today())
					if float_is_zero(amount_to_show, precision_rounding=self.currency_id.rounding):
						continue
					if line.ref :
						title = '%s : %s' % (line.move_id.name, line.ref)
					else:
						title = line.move_id.name
					info['content'].append({
						'journal_name': line.ref or line.move_id.name,
						'journal_id': line.ref or line.move_id.id,
						'title': title,
						'amount': amount_to_show,
						'currency': currency_id.symbol,
						'id': line.id,
						'position': currency_id.position,
						'digits': [69, self.currency_id.decimal_places],
					})
				info['title'] = type_payment

			return info
AccountInvoiceInherit()