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

from odoo.exceptions import UserError, ValidationError


class EditMethodPayment(models.TransientModel):
	_name = "edit.payment_method"

	journal_id = fields.Many2one('account.journal', string="Metodo de pago", domain="[('journal_user', '=', True)]")

	@api.onchange('journal_id')
	def onchange_journal(self):

		#obteniendo datos por contexto
		journal_id = self._context.get('ctx_journal_id')

		if journal_id == self.journal_id.id:
			msg = _(u'Alerta! Seleccione otro medio de pago. \n El medio de pago a cambiar es el mismo que esta registrado.')
			raise ValidationError(msg)


	@api.multi
	def change_payment_method(self):

		#obteniendo datos por contexto
		name = self._context.get('ctx_name')
		amount = self._context.get('ctx_amount')
		partner_id = self._context.get('ctx_partner_id')
		ref = self._context.get('ctx_ref')
		pos_statement_id = self._context.get('ctx_pos_statement_id')
		payment_id = self._context.get('ctx_payment_id')
		journal_id = self._context.get('ctx_journal_id')

		model_bank_statement = self.env['account.bank.statement.line']
		model_pos_session = self.env['pos.session']


		if journal_id == self.journal_id.id:
			msg = _(u'Alerta! Seleccione otro medio de pago. \n El medio de pago a cambiar es el mismo que esta registrado.')
			raise ValidationError(msg)
		else:

			if ref:
				session_id = model_pos_session.search([('name', '=', ref)])
				if session_id.state in ['opening_control', 'opened']:

					if payment_id:
						record = model_bank_statement.search([('id', '=', payment_id)])
						
						if session_id:
							for x in session_id.statement_ids:
								if self.journal_id.id == x.journal_id.id:
									model_bank_statement.sudo().create({

										'name': name,
										'amount':amount,
										'partner_id': partner_id or False,
										'ref': ref,
										'statement_id': x.id,
										'pos_statement_id': pos_statement_id,
										'account_id': self.env['account.account'].search([('code', '=', '130505')], limit=1).id,
										'date': fields.Date.today()
										})

						record.unlink()

EditMethodPayment()