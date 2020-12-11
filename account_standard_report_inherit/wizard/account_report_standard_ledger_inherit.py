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
from odoo.exceptions import AccessError, UserError
import logging
_logger = logging.getLogger(__name__)

class AccountStandardLedgerInherit(models.TransientModel):
	
	_inherit = 'account.report.standard.ledger'


	parent_account_id = fields.Many2one('account.account', 'Parent Account')
	parent_account_ids = fields.Many2many('account.account', 'report_standard_legder_account_account_rel', column1='standard_legerd_id', column2="account_id", string="Cuentas")


	def upload_data_account_ids(self, parent_account_ids):
		data=[]
		data_ids=[]

		if parent_account_ids:


			sql_parent_account_ids = ''
			for x in parent_account_ids:
				sql_parent_account_ids += " code LIKE '" + str(x.code) + "%' OR"
			
			sql = "SELECT id AS account_id FROM account_account WHERE "
			sql = sql + sql_parent_account_ids[:len(sql_parent_account_ids)-2]
			self.env.cr.execute(sql)
	
			res = self.env.cr.dictfetchall()

			children_ids = res

			if children_ids:
				for x in children_ids:
					data_ids.append(x['account_id'])
					
			data.append((6, 0, data_ids))
		
			return data

	@api.onchange('parent_account_ids')
	def onchange_parent_id(self):

		if self.parent_account_ids:
			self.account_in_ex_clude_ids= self.upload_data_account_ids(self.parent_account_ids)
		else:
			self.account_in_ex_clude_ids = None

