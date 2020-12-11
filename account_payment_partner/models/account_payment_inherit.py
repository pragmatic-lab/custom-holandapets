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
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import logging
_logger = logging.getLogger(__name__)
import json


class AccountPaymentInherit(models.Model):
	
	_inherit = 'account.payment'

	@api.multi
	@api.depends('register_payments_ids')
	def compute_value_register_payments(self):
		"""
			Funcion que permite saber el total de los pagos que se estan o se han agregado al pago
		"""
		amount_total = 0
		if self.register_payments_ids:
			for x in self.register_payments_ids:
				amount_total += x.amount or 0

		self.payment_current_amount = amount_total



	@api.multi
	def compute_value_amount_payments(self):
		"""
			Funcion que permite saber cuanto es el credito que le va quedando al pago actual
		"""
		payment_total = 0
		move_name = self.move_name
		credit_aml_id = self.return_credit_aml_id(self.partner_id.supplier)
		account_ml = self.env['account.move.line'].search([('id', '=', credit_aml_id)])

		if account_ml:
			self.payment_amount_total = account_ml.amount_residual
		else:
			self.payment_amount_total = self.amount

										
	@api.onchange('partner_id', 'partner_type')
	def onchange_partner_type_partner(self):
		"""
			Onchange que sirve para realizar un domain al campo payment_partner_id para filtrar si es proveedor o cliente
		"""
		self.ensure_one()
		# Set partner_id domain
		if self.partner_type:
			return {'domain': {'payment_partner_id': [(self.partner_type, '=', True)]}}


	@api.onchange('payment_invoices')
	def onchange_payment_invoices(self):
		"""
			Funcion que permite validar si el pago a registrar es mayor que 0
		"""
		if self.payment_invoices:
			if self.amount < 1:
				raise Warning(_('No puede iniciar una acreditación de pagos con la Cantidad a Pagar en 0. \n Si cree que esto es un error. Por favor comuniquese con el Administrador'))

			
	payment_invoices = fields.Boolean(string="Pagar Facturas", default=False)

	payment_partner_id = fields.Many2one('res.partner', string="Tercero")
	partner_register_ids = fields.One2many('account.payment_partner_register', 'account_payment_id', string="Pagos")
	register_payments_ids = fields.One2many('account.payment_partner_register', 'register_payment_id', string="Pagos a Realiar")
	payment_amount_total = fields.Float(string="Total", compute='compute_value_amount_payments')
	payment_current_amount = fields.Float(string="Total", compute='compute_value_register_payments')

	@api.onchange('payment_partner_id')
	def onchange_payment_partner_id(self):
		"""
			Funcion que permite cargar todas las facturas del tercero que no esten totalmente pagas
		"""
		if self.payment_partner_id:
			model_invoice = self.env['account.invoice']
			invoice_ids = model_invoice.search([('partner_id', '=', self.payment_partner_id.id), ('state', 'not in', ['cancel', 'paid'])])

			#_logger.info('las facturas son')
			#_logger.info(invoice_ids)

			data = []

			if invoice_ids:
				for x in invoice_ids:
	
					vals = {
						'invoice_id' : x.id
					}

					data.append((0,0, vals))
			self.partner_register_ids = None
			self.partner_register_ids = data


	def load_register_payments_ids(self):
		"""
			Funcion que permite cargar los pagos a realizar con el respectivo monto
		"""
		amount_credit = self.payment_amount_total
		amount_current = self.payment_current_amount


		sum_amount_current = 0

		data = []
		if self.partner_register_ids:
			for x in self.partner_register_ids:
				if x.amount and x.amount > 0:
					sum_amount_current += x.amount
					vals = {
						'invoice_id' : x.invoice_id.id,
						'amount': x.amount,
					}

					data.append((0,0, vals))

		validate_amount_current= sum_amount_current + amount_current

		if validate_amount_current > amount_credit:
			raise Warning(_('No se pueden cargar todos lo pagos, ya que sobre pasa el valor del crédito. \n Actualmente tiene: \n -> Valor Crédito: $' + str(amount_credit) + '\n -> Valor Facturas a Cargar: $'+ str(sum_amount_current) + '\n -> Saldo Actual: $'+ str(amount_current) + '\n Si cree que esto es un error. Por favor comuniquese con el Administrador'))
		else:
			self.register_payments_ids = data

		self.partner_register_ids = None

		return {'domain': {'payment_partner_id': [(self.partner_type, '=', True)]}}


	def return_credit_aml_id(self, type_partner):
		"""
			Funcion que permite retornar el id del apunte contable asociado al pago
		"""

		account_payment_id = self.id

		domain = [('payment_id', '=', self.id)]

		if type_partner == False:
			domain.append(('debit', '=', 0))
		else:
			domain.append(('debit', '!=', 0))

		account_ml = self.env['account.move.line'].search(domain)
		_logger.info('la vaina esta en essto')
		_logger.info(account_ml)

		if account_ml:
			#_logger.info('aqui')
			#_logger.info(account_ml[0].name)

			move_id = account_ml[0].id

			return move_id

		return -1

	def return_credit_aml_by_partner(self, type_partner, partner_id, amount, data_aml):
		"""
			Funcion que permite retornar el id del apunte contable asociado al pago
		"""


		account_payment_id = self.id

		domain = [('payment_id', '=', self.id), ('partner_id', '=', partner_id)]

		if type_partner == False:
			domain.append(('debit', '=', 0))
			domain.append(('credit', '=', amount))
		else:
			domain.append(('debit', '!=', 0))
			domain.append(('debit', '=', amount))

		account_ml = self.env['account.move.line'].search(domain)

		data = []
		if account_ml:
			#_logger.info('aqui')
			#_logger.info(account_ml[0].name)
			if len(account_ml) > 1:
				for x in account_ml:
					if x.id not in data_aml:
						
						data_aml.append(x.id)
						#move_id = account_ml[0].id
						return x.id
			else:

				return account_ml[0].id

		return -1



	def return_amount_total_payments(self):
		"""
			Funcion que permite validar si el valor total de las facturas a pagar sea igual 
			que el monto del credito o cantidad a pagar
		"""	
		if self.payment_invoices:
			amount_credit = self.payment_amount_total
			sum_amount_current = 0
			if self.register_payments_ids:
				for x in self.register_payments_ids:

					sum_amount_current+= x.amount

				if sum_amount_current != self.amount:
					raise Warning(_('No se puede realizar los respectivos pagos a la facturas. \n Actualmente tiene: \n \t -> Valor Crédito: $' + str(amount_credit) +  '\n \t-> Saldo Actual: $'+ str(sum_amount_current) + ' \n El valor del Crédito y el Saldo Actual deben ser iguales para procesar los pagos. \n Si cree que esto es un error. Por favor comuniquese con el Administrador'))
			else:
				raise Warning(_('No se puede realizar los respectivos pagos a la facturas. \n Actualmente no tiene nigún pago de factura alistado:' + ' \n El valor del Crédito y el Saldo Actual deben ser iguales para procesar los pagos. \n Si cree que esto es un error. Por favor comuniquese con el Administrador'))
				



	def payment_quick_invoice(self):
		"""
			Funcion que permite realizar el pago respectivo por cada factura
		"""
		self.return_amount_total_payments()
		data_partner = []

		data_aml = []

		if self.register_payments_ids:
			for x in self.register_payments_ids:
				if x.state == False:

					if x.invoice_id.partner_id.id not in data_partner:
						data_partner.append(x.invoice_id.partner_id.id)

					invoice = x.invoice_id
					
					credit_aml_id = self.return_credit_aml_by_partner(invoice.partner_id.supplier, invoice.partner_id.id, x.amount, data_aml)


					print('Pagando Factura: ' + str(invoice.number) + ' el credit_aml_id es: ' + str(credit_aml_id) + ' ' + str(x.amount))
			
					invoice.with_context(paid_amount=x.amount).assign_outstanding_credit(credit_aml_id)
					x.write({'state': True})



	def update_partner_data(self, data, partner_id, amount):
		"""
			Funcion que permite actualizar el valor del amount en la data
		"""
		if data:
			for x in data:
				if x['partner_id'] == partner_id:
					x['amount'] += amount



	def search_partner_data(self, data, partner_id):
		"""
			Funcion que permite validar si ya existe el partner en la data
		"""
		if data:
			if len(data) > 0:
				for x in data:
					if x['partner_id'] == partner_id:
						return True
		return False

	def return_partner_payment_data(self):
		"""
			Funcion que permite retornar el total a pagar por tercero
		"""
		data = []
		if self.register_payments_ids:

			for x in self.register_payments_ids:
				partner_id = x.invoice_id.partner_id.id
				vals = {
				'partner_id': partner_id,
				'amount': x.amount
				}
				data.append(vals)
				# if self.search_partner_data(data, partner_id) == False:
			
				# 	vals = {
				# 		'partner_id': partner_id,
				# 		'amount': x.amount
				# 	}
			
				# 	data.append(vals)

				# else:

				# 	self.update_partner_data(data, partner_id, x.amount)					
		return data


	def return_data_account_ml(self, val, aml_obj):
		"""
			Funcion que retorna el vals cmopleto para poder realizar el apunte contable por cada partner
			que se utilizo para el pago de las facturas
		"""

		if val:

			partner_payment_data = self.return_partner_payment_data()

			for x in partner_payment_data:
				val_new = val
				val_new['partner_id'] = x['partner_id']
				val_new['debit'] = x['amount']
				print('modificando el val')
				print(val_new)
				#aml_obj.create(x)



	def _create_payment_entry(self, amount):
		""" Create a journal entry corresponding to a payment, if the payment references invoice(s) they are reconciled.
			Return the journal entry.
		"""

		# print('este es el valor del pago')
		# print(amount)
		# print(self)
		# print(self._get_move_vals())
		# print(self.env.context)
		aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
		debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amount, self.currency_id, self.company_id.currency_id)

		move = self.env['account.move'].create(self._get_move_vals())

		# print('creando asiento contable')
		# print(move)
		# print(move.line_ids)

		#Write line corresponding to invoice payment
		counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
		print('first: ' + str(counterpart_aml_dict))
		counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.invoice_ids))
		print('second: ' + str(counterpart_aml_dict))
		counterpart_aml_dict.update({'currency_id': currency_id})
		print('third: ' + str(counterpart_aml_dict))

		counterpart_aml = None
		if self.payment_invoices and self.register_payments_ids:   
			val = counterpart_aml_dict
			#counterpart_aml = aml_obj.create(counterpart_aml_dict)


			partner_payment_data = self.return_partner_payment_data()

			data = []
			for x in partner_payment_data:

				partner_id = self.env['res.partner'].search([('id', '=', counterpart_aml_dict['partner_id'])])
				
				if partner_id:
					vals = {
						'partner_id': x['partner_id'],
						'invoice_id': counterpart_aml_dict['invoice_id'],
						'move_id': counterpart_aml_dict['move_id'],
						'amount_currency': counterpart_aml_dict['amount_currency'],
						'payment_id': counterpart_aml_dict['payment_id'],
						'journal_id':  counterpart_aml_dict['journal_id'],
						'name': counterpart_aml_dict['name'],
						'account_id': counterpart_aml_dict['account_id'], 
						'currency_id': counterpart_aml_dict['currency_id']
					}

					if partner_id.supplier:

						vals['debit']= x['amount']
						vals['credit']= counterpart_aml_dict['credit']

					else:

						vals['debit']= counterpart_aml_dict['debit']
						vals['credit']= x['amount']

					data.append(vals)

			for x in data:
				_logger.info(x)
				counterpart_aml = aml_obj.create(x)
		else:
			counterpart_aml = aml_obj.create(counterpart_aml_dict)



		# print('listos')
		# val1 = counterpart_aml_dict
		# val1['debit'] = 25000
		# print(val1)
		#counterpart_aml = aml_obj.create(counterpart_aml_dict)
		# val2 = counterpart_aml_dict
		# val2['partner_id'] = 12
		# val2['debit'] = 20000


		# print(val2)
		
		# counterpart_amll = aml_obj.create(val2)

		#Reconcile with the invoices
		if self.payment_difference_handling == 'reconcile' and self.payment_difference:
			writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
			debit_wo, credit_wo, amount_currency_wo, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(self.payment_difference, self.currency_id, self.company_id.currency_id)
			writeoff_line['name'] = self.writeoff_label
			writeoff_line['account_id'] = self.writeoff_account_id.id
			writeoff_line['debit'] = debit_wo
			writeoff_line['credit'] = credit_wo
			writeoff_line['amount_currency'] = amount_currency_wo
			writeoff_line['currency_id'] = currency_id
			writeoff_line = aml_obj.create(writeoff_line)
			if counterpart_aml['debit'] or (writeoff_line['credit'] and not counterpart_aml['credit']):
				counterpart_aml['debit'] += credit_wo - debit_wo
			if counterpart_aml['credit'] or (writeoff_line['debit'] and not counterpart_aml['debit']):
				counterpart_aml['credit'] += debit_wo - credit_wo
			counterpart_aml['amount_currency'] -= amount_currency_wo

		#Write counterpart lines
		if not self.currency_id.is_zero(self.amount):
			if not self.currency_id != self.company_id.currency_id:
				amount_currency = 0
			liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
			liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
			aml_obj.create(liquidity_aml_dict)

		#validate the payment
		if not self.journal_id.post_at_bank_rec:
			move.post()

		#reconcile the invoice receivable/payable line(s) with the payment
		if self.invoice_ids:
			self.invoice_ids.register_payment(counterpart_aml)

		return move



	@api.multi
	def post(self):
		"""
			Sobreescribiendo la funcion que permite confirmar el pago, se valida que el valor del saldo actual
			sea igual al del pago
		"""
		self.return_amount_total_payments()
		res = super(AccountPaymentInherit, self).post()
		self.payment_quick_invoice()
		return res


AccountPaymentInherit()



