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
from math import sqrt
import statistics as stats
import math
import threading

class LimitCreditPartner(models.Model):

	_name = 'limit.credit_partner'
	_rec_name = 'partner_id'


	#name = fields.Char(string= u"Código", store=True, readonly=True)
	partner_id = fields.Many2one("res.partner", string= u"Cliente", store=True, readonly=True)
	credit = fields.Float(string= u"Crédito", store=True, readonly=True)	
	debit = fields.Float(string= u"Débito", store=True, readonly=True)
	sale_order_id =  fields.Many2one('sale.order', string= u"Orden de Venta", store=True, readonly=True)
	payment_order =  fields.Float(string= u"Total Orden de Venta", compute= '_compute_payment_order')
	payment_id =  fields.Many2one('account.payment', string= u"Descripción Pago", store=True, readonly=True)
	payment =  fields.Float(string= u"Pagos", store=True, readonly=True)
	registration_day = fields.Datetime('Date current action', select=True , default=lambda self: fields.datetime.now(), store=True, readonly=True)

	@api.one
	def _compute_payment_order(self):

		if self.sale_order_id:
			self.payment_order = self.sale_order_id.amount_total
	
	def return_vals_limit_credit(self, partner_id, credit, debit, payment_id, payment, sale_order_id):
		
		vals= {
		'partner_id': partner_id,
		'credit': credit,
		'debit': debit,
		'payment_id':payment_id,
		'payment': payment,
		'sale_order_id': sale_order_id
		}

		return vals


	def create_limite_credit(self, partner_id, credit, debit, payment_id, payment, sale_order_id):
		"""
			Función que permite crear un registro del movimiento del crédito del partner
		"""
		if partner_id:
		
			self.create(self.return_vals_limit_credit(partner_id, credit, debit, payment_id, payment, sale_order_id))


	def return_last_credit_partner_data(self, partner_id):

		"""
			Funcion que permite retornar el ultimo registro de actividad de credito filtrado por un partner o cliente
			especifico
		"""

		if partner_id:

			limit_credit_partner_id = self.search([('partner_id', '=', partner_id)], limit= 1, order= 'registration_day desc')

			vals = {
				'partner_id': limit_credit_partner_id.partner_id,
				'credit': limit_credit_partner_id.credit,
				'debit': limit_credit_partner_id.debit,
				'payment_id': limit_credit_partner_id.payment_id,
				'payment': limit_credit_partner_id.payment,
				'registration_day': limit_credit_partner_id.registration_day,
				'sale_order_id': limit_credit_partner_id.sale_order_id
			}


			return vals


	def update_credit_limit_partner(self, partner_id, amount_total, option, payment_id, sale_order_id):

		"""
			Funcion que permite calcular el credito y el bedito del cliente.
		"""

		if partner_id:

			amount_total = amount_total

			data_credit_partner = self.return_last_credit_partner_data(partner_id)

			credit_previous = data_credit_partner['credit']
			debit_previous = data_credit_partner['debit']
			payment_previous = data_credit_partner['payment']
			update_payment = 0

			update_credit = credit_previous - amount_total
			update_debit = debit_previous + amount_total

			if option == 1:
				_logger.info('entramos nada mas a pagar')
				update_credit = credit_previous + amount_total
				update_debit = debit_previous - amount_total
				update_payment = payment_previous + amount_total

			self.create_limite_credit(partner_id, update_credit, update_debit, payment_id, update_payment, sale_order_id)



	def update_partner_credit(self, partner_id, amount_total, sale_order_id):

		"""
			Funcion que permite calcular aumentar el credito del partner, como también en el detalle de credito del mismo
		"""
		model_credit_limit = self.env['limit.credit']
		if partner_id:

			#amount_total = amount_total

			data_credit_partner = self.return_last_credit_partner_data(partner_id)

			credit_previous = data_credit_partner['credit']
			debit_previous = data_credit_partner['debit']
			payment_id_previous = data_credit_partner['payment_id']
			payment_previous = data_credit_partner['payment']
			#sale_order_id_previous = data_credit_partner['sale_order_id']


			#balance = float(amount_total - credit_previous)

			balance = float( credit_previous - amount_total)


			flag = 0
			credit_add = 0
				

			if balance < 0:
				credit_add = -balance
				flag= 0
			else:
				credit_add = balance
				flag = balance


			search_partner_id = self.env['res.partner'].search([('id', '=', partner_id)])
			_logger.info('sdfs------------------')
			_logger.info(search_partner_id)
			
			#se actualiza el valor del partner
			for x in search_partner_id:
				x.write({'limit_credit': float(x.limit_credit + credit_add)})

			#se actualiza el valor del credito
			for x in model_credit_limit.search([('partner_id', '=', partner_id)]):
				x.write({'credit': float(x.credit + credit_add)})


			self.create_limite_credit(partner_id, flag, debit_previous + amount_total, payment_id_previous, payment_previous, sale_order_id)
			#self.create_limite_credit(partner_id, update_credit, update_debit, payment_id, update_payment, sale_order_id)
			limit_credit = model_credit_limit.search([('partner_id', '=', self.id)], limit= 1, order= 'registration_day desc')
			limit_credit.write({'credit': flag})

LimitCreditPartner()





