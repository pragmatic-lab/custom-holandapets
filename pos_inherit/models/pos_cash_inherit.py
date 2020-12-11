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
from odoo.addons.account.wizard.pos_box import CashBox
import logging
_logger = logging.getLogger(__name__)


class PosBox(CashBox):
	_register = False

	code = fields.Char(string="Vendedor")
	user_id = fields.Many2one('res.users', string="Vendedor")
	partner_id = fields.Many2one('res.partner', string="Tercero")
	account_id = fields.Many2one('account.account', string="Cuenta")
	pos_session_id = fields.Many2one('pos.session', string="Pos Session")

PosBox()

class PosCashInInherit(PosBox):
	_inherit = "cash.box.in"

	@api.model
	def create(self, vals):

		pos_session_id =self.env.context.get('pos_session_id')

		if pos_session_id:
			vals['pos_session_id'] = pos_session_id

		vals['code'] = self.env['ir.sequence'].next_by_code('pos.cash.in')
	
		res = super(PosCashInInherit, self).create(vals)
		return res


PosCashInInherit()

class PosCashOutInherit(PosBox):
	_inherit = "cash.box.out"

	@api.model
	def create(self, vals):
		pos_session_id =self.env.context.get('pos_session_id')
		_logger.info('Pos session')
		_logger.info(pos_session_id)

		if pos_session_id:
			vals['pos_session_id'] = pos_session_id

		vals['code'] = self.env['ir.sequence'].next_by_code('pos.cash.out')

		res = super(PosCashOutInherit, self).create(vals)
		return res


PosCashOutInherit()
