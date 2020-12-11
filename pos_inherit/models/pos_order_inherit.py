# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from datetime import timedelta
from functools import partial

import psycopg2
import pytz

from odoo import api, fields, models, tools, _
from odoo.tools import float_is_zero
from odoo.exceptions import UserError
from odoo.http import request
from odoo.addons import decimal_precision as dp

_logger = logging.getLogger(__name__)



class PosOrderInherit(models.Model):
	_inherit = "pos.order"




	@api.model
	def _process_order(self, pos_order):
		"""
			Se reemplaza esta funcion para remover la devolucion del pago realizado, con lo cual
			solamente quedara registrado un solo pago.
		"""
		pos_session = self.env['pos.session'].browse(pos_order['pos_session_id'])
		if pos_session.state == 'closing_control' or pos_session.state == 'closed':
			pos_order['pos_session_id'] = self._get_valid_session(pos_order).id

		print('estos es lo primero')
		print(self._order_fields(pos_order))
		order = self.create(self._order_fields(pos_order))
		prec_acc = order.pricelist_id.currency_id.decimal_places
		journal_ids = set()
		for payments in pos_order['statement_ids']:
			if not float_is_zero(payments[2]['amount'], precision_digits=prec_acc):
				print('Esto es lo segundo')
				print(self._payment_fields(payments[2]))
				vals = self._payment_fields(payments[2])
				vals['amount'] = vals['amount'] -pos_order['amount_return']
				order.add_payment(vals)
			journal_ids.add(payments[2]['journal_id'])

		if pos_session.sequence_number <= pos_order['sequence_number']:
			pos_session.write({'sequence_number': pos_order['sequence_number'] + 1})
			pos_session.refresh()

		if not float_is_zero(pos_order['amount_return'], prec_acc):
			cash_journal_id = pos_session.cash_journal_id.id
			if not cash_journal_id:
				# Select for change one of the cash journals used in this
				# payment
				cash_journal = self.env['account.journal'].search([
					('type', '=', 'cash'),
					('id', 'in', list(journal_ids)),
				], limit=1)
				if not cash_journal:
					# If none, select for change one of the cash journals of the POS
					# This is used for example when a customer pays by credit card
					# an amount higher than total amount of the order and gets cash back
					cash_journal = [statement.journal_id for statement in pos_session.statement_ids if statement.journal_id.type == 'cash']
					if not cash_journal:
						raise UserError(_("No cash statement found for this session. Unable to record returned cash."))
				cash_journal_id = cash_journal[0].id
			print('esto es lo ultimo')
			print(-pos_order['amount_return'])

		return order