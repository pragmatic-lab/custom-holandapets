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
from odoo.osv import osv

class SaleOrderInherit(models.Model):

	_inherit = "sale.order"

	limit_credit = fields.Boolean(string= u"Límite Crédito")
	state = fields.Selection([
		('draft', 'Quotation'),
		('sent', 'Quotation Sent'),
		('limit_credit', 'Limit Credit'),
		('sale', 'Sales Order'),
		('done', 'Locked'),
		('cancel', 'Cancelled'),
		], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')
	


	def calculate_limit_credit_partner(self):
		
		"""
			Funcion que permite calcular el límite del crédito del cliente que tiene actualmente
		"""

		flag = True

		model_credit_limit = self.env['limit.credit_partner']

		if self.partner_id:

			_logger.info(self.partner_id.limit_credit)

			if self.partner_id.limit_credit > 0:

				_logger.info('entramos por aca')

				data_credit_partner = model_credit_limit.return_last_credit_partner_data(self.partner_id.id)

				#balance = data_credit_partner['credit'] - data_credit_partner['debit']
				#balance = balance + data_credit_partner['payment']

				_logger.info(data_credit_partner['credit'])

				if data_credit_partner['credit'] <= 0:
	
					flag=False
				else:

					if (data_credit_partner['credit'] - self.amount_total) < 0:
						flag=False

		return flag


	@api.onchange('partner_id')
	def onchange_partner_limit_credit(self):
		
		self.env['res.partner'].know_blocking(self.partner_id)

		if self.calculate_limit_credit_partner() == False:

			raise osv.except_osv(_('Alerta!'), _('El cliente %s, ya no cuenta con un crédito suficiente o ha sobrepasado su crédito permitido. \n Por favor aumentar el crédito del cliente') % self.partner_id.name)



	def return_update_state(self, state):
		self.write({'state': state, 'confirmation_date': fields.Datetime.now()})


	def return_confirm_sale_order(self):
		self._action_confirm()
		if self.env['ir.config_parameter'].sudo().get_param('sale.auto_done_setting'):
			self.action_done()


	@api.multi
	def action_confirm(self):

		model_credit_limit = self.env['limit.credit_partner']
		_logger.info('Hola como esta')
		_logger.info(self.state)

		if self._get_forbidden_state_confirm() & set(self.mapped('state')):
			raise UserError(_(
				'It is not allowed to confirm an order in the following states: %s'
			) % (', '.join(self._get_forbidden_state_confirm())))

		for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
			order.message_subscribe([order.partner_id.id])


		# el cliente tiene credito
		# el usuario le aumenta el credito 
		# el cliente no tiene credito

		#tiene credito
		if self.calculate_limit_credit_partner():

			_logger.info('tiene credito')
			self.return_update_state('sale')
			self.return_confirm_sale_order()
			model_credit_limit.update_credit_limit_partner(self.partner_id.id, self.amount_total, 0, None, self.id)

		else:
			#no tiene credito
			update_credit  =self.env.context.get('update_limit_credit')
			# el usuario le aumenta el credito
			if update_credit:
				if self.user_has_groups('limit_credit_partner.group_conf_limit_credit'):
					_logger.info('estamos actulizando el credito')
					self.return_update_state('sale')
					self.return_confirm_sale_order()
					model_credit_limit.update_partner_credit(self.partner_id.id, self.amount_total, self.id)
					self.write({'limit_credit': False})
			else:

				self.return_update_state('limit_credit')
				self.write({'limit_credit': True})
				#raise osv.except_osv(_('Alerta!'), _('El cliente %s, ya no cuenta con un crédito suficiente o ha sobrepasado su crédito permitido. \n Por favor aumentar el crédito del cliente') % self.partner_id.name)

		return True


SaleOrderInherit()