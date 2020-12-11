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
                            
class AccountBankStatementLineinherit(models.Model):
	_inherit = "account.bank.statement.line"


	@api.multi
	def button_go_change_payment(self):
		"""
			Función que permite llevar hasta el wizard para cambiar el metodo de pago
		"""
		context = self.env.context.copy()
		context.update({'ctx_payment_id': self.id,
						'ctx_name': self.name,
						'ctx_amount': self.amount,
						'ctx_partner_id': self.partner_id.id,
						'ctx_ref': self.ref,
						'ctx_journal_id': self.journal_id.id,
						'ctx_pos_statement_id': self.pos_statement_id.id
						}) 
		model_pos_session = self.env['pos.session']
		session_id = model_pos_session.search([('name', '=', self.ref)])
		if session_id.state in ['opening_control', 'opened']:

			return {
				'name': _(u'Cambio de Método de Pago'),
				'type':'ir.actions.act_window',
				'res_model':'edit.payment_method',
				'view_type':'form',
				'view_mode':'form',
				'target':'new',
				'nodestroy': True,
				'res_id': False,
				'context': context
			}
		else:
			msg = _(u'Alerta! No se puede cambiar el método de pago, la sessión ya esta cerrada.')
			raise ValidationError(msg)

AccountBankStatementLineinherit()
