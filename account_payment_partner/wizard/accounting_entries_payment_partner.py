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


from datetime import datetime, timedelta
from odoo import api, models, fields, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import logging
_logger = logging.getLogger(__name__)

class AccountingEntriespaymentpartner(models.Model):
	
	_name = 'account.entries_payment_partner'
	_rec_name = 'move_id'
	_order = 'move_id desc'

	@api.depends('move_id')
	def _compute_amount_payment(self):
		"""
			Funcion que permite cargar:
				-> Valor de la factura
				-> Total pagado
				-> Total adeudado
		"""
		data = self.return_account_move_line_available_partner()
		amount_current = 0
		for x in data:
			amount_current += x['amount']

		for x in self:
			move_id = x.move_id
			x.amount = move_id.amount
			x.amount_current = amount_current


	partner_type = fields.Selection([('customer', 'Cliente'), ('supplier', 'Proveedor')], string="Tipo de Empresa", required=True, default='customer')
	journal_id = fields.Many2one('account.journal', string='Diario', required=True)
	move_id = fields.Many2one('account.move', string="Asiento Contable", required=True)
	payment_partner_id = fields.Many2one('res.partner', string="Tercero")
	partner_register_ids = fields.One2many('account.payment_partner_register', 'account_entries_payment_id', string="Pagos")
	register_payments_ids = fields.One2many('account.payment_partner_register', 'register_entries_payment_id', string="Pagos a Realiar")
	amount= fields.Float(string=u"Total Monto", compute='_compute_amount_payment')
	html_info = fields.Html(string="Html", readonly=True, store=True)
	amount_current = fields.Float(string="Total", compute='_compute_amount_payment')
	


	def return_validation_partner_type_customer(self):
		"""
			Funcion que permite verificar si es un cliente o un proveedor
		"""
		if self.partner_type:
			if self.partner_type == 'customer':
				return True
			else:
				return False

		return -1


	@api.depends('partner_type', 'journal_id')
	@api.onchange('partner_type', 'journal_id')
	def onchange_partner_type(self):
		"""
			Funcion que permite cargar los asientos contables de acuerdo al tipo de empresa,
			es decir, si es proveedor o cliente.
		"""

		account_move_ids = self.env['account.move'].search([('journal_id', '=', self.journal_id.id)])
		data_move = []
		if account_move_ids:
			for x in account_move_ids:
				if x.line_ids:
					for line in x.line_ids:
						if line.partner_id.customer == self.return_validation_partner_type_customer():
							if x.id not in data_move:
								data_move.append(x.id)

		return {'domain': {'move_id': [('id', 'in', data_move)]}}

	def return_data_partner_move(self, partner_type):
		"""
			Funcion que permite retornar los ids de los terceros que estan en el asiento contable
		"""
		data_partner = []
		for x in self.move_id:
			if x.line_ids:
				for line in x.line_ids:
					
					if line.partner_id.id not in data_partner:
						data_partner.append(line.partner_id.id)


		return data_partner




	def return_data_partner_invoice(self, data_partner):
		"""
			Funcion que retorna las facturas del cliente seleccionado
		"""

		data = []

		if self.payment_partner_id:
			model_invoice = self.env['account.invoice']
			invoice_ids = None
			if data_partner:
				invoice_ids = model_invoice.search([('partner_id', 'in', data_partner), ('state', 'not in', ['cancel', 'paid'])])

			else:
				invoice_ids = model_invoice.search([('partner_id', '=', self.payment_partner_id.id), ('state', 'not in', ['cancel', 'paid'])])

			if invoice_ids:
				for x in invoice_ids:
	
					vals = {
						'invoice_id' : x.id,
					}
					data.append((0,0, vals))





		return data

	def create_amount_partner_available(self):
		"""
			Funcion que permite crear los creditos disponibles, estos apareceran para que el usuario pueda seleccionar cualquiera
		"""

		data_amount = self.return_account_move_line_available_partner()

		model_account_payment_partner_amount = self.env['account.payment_partner_amount']

		data = []
		if self.register_payments_ids:
			for x in self.register_payments_ids:
				data.append(x.acount_ml_amount_id.account_ml_id.id)

		print('la data es')
		print(data)
		for x in data_amount:
			if x['account_ml_id'] not in data:
				print(x)
				model_account_payment_partner_amount.create(x)

	def delete_amount_partner_available(self, option):
		"""
			Funcion que permite eliminar todos los creditos disponibles
		"""

		sql="""
			DELETE FROM account_payment_partner_amount 
		"""
		sql_where = ""
		if self.register_payments_ids:

			for x in self.register_payments_ids:
				if x.state == False:
					sql_where += str(x.acount_ml_amount_id.account_ml_id.id) + ', '

					sql += 'WHERE account_ml_id not in (' + str(sql_where)[:len(sql_where)-2] + ')'

		if option:

			for x in option:
				sql_where += str(x) + ', '

			sql += 'WHERE account_ml_id in (' + str(sql_where)[:len(sql_where)-2] + ')'

		print(sql)

		try:
			self.env.cr.execute( sql )
		except Exception as e:
			raise Warning(_('Ha ocurrido un error mientras se eliminaba los creditos disponibles. \n Si cree que esto es un error. Por favor comuniquese con el Administrador'))




	def return_account_move_line_available_partner(self):
		"""
			Funcion que permite retornar los creditos disponibles del partner
		"""
		data_amount = []

		for aml in self.move_id.line_ids:

			ids = []

			if aml.account_id.reconcile:
				ids.extend([r.debit_move_id.id for r in aml.matched_debit_ids] if aml.credit > 0 else [r.credit_move_id.id for r in aml.matched_credit_ids])
				ids.append(aml.id)

			if len(ids) == 1:
				type_partner = aml.partner_id.supplier

				amount = 0
				if type_partner == False:
					amount = aml.credit
				else:
					amount = aml.debit

				vals = {
					'account_ml_id': aml.id,
					'amount': amount
				}
				data_amount.append(vals)
	
		return data_amount


	@api.onchange('move_id')
	def onchange_move_id(self):
		"""
			Funcion que permite cargar los terceros disponibles para el respectivo asiento contable
		"""

		print('entrando en el onchange de move_id')

		#eliminando los amount disponibles
		self.delete_amount_partner_available(False)


		#creando amounts para pagar
		self.create_amount_partner_available()

		data_partner = self.return_data_partner_move(self.partner_type)

		data = self.return_data_partner_invoice(data_partner)

		self.partner_register_ids = None
		self.partner_register_ids = data


		data_s =""
		ul = """
				<ul class="list-group" style="display: inline-block; width:230px;">
				  <li class="list-group-item d-flex justify-content-between align-items-center" style="font-size:11px;">
				    %(name_move)s
				    <span class="badge badge-primary badge-pill" style="font-size:12px;">%(move_amount)s</span>
				  </li>
				</ul>
		"""

		for aml in self.move_id.line_ids:
			print('******')
			ids = []


			if aml.account_id.reconcile:
				ids.extend([r.debit_move_id.id for r in aml.matched_debit_ids] if aml.credit > 0 else [r.credit_move_id.id for r in aml.matched_credit_ids])
				ids.append(aml.id)

			if len(ids) == 1:

				type_partner = aml.partner_id.supplier

				amount = 0
				if type_partner == False:
					amount = aml.credit
				else:
					amount = aml.debit

				data_s += ul%{
						'name_move':aml.partner_id.name,
						'move_amount': amount
				}

	
				print(ids)

		self.html_info = data_s
		

		context = self.env.context.copy()
		context.update( { 'move_id': self.move_id.id }) 
		return {'domain': {'payment_partner_id': [('id', 'in', data_partner)]}}



	@api.onchange('payment_partner_id')
	def onchange_payment_partner_id(self):
		"""
			Funcion que permite cargar todos los asientos contables del tercero
		"""
		print('entrando en el onchange de partner_id')
		data = self.return_data_partner_invoice(False)

		self.partner_register_ids = None
		self.partner_register_ids = data
		return {'context': {'move_id': self.move_id.id}}

	def load_register_payments_ids(self):
		"""
			Funcion que permite cargar los pagos a realizar con el respectivo monto
		"""

		self.validate_load_invoice_payment()

		sum_amount_current = 0

		data = []
		if self.partner_register_ids:
			for x in self.partner_register_ids:
				print('entrando ando')
				if x.acount_ml_amount_id:
					sum_amount_current += x.acount_ml_amount_id.amount
					vals = {
						'invoice_id' : x.invoice_id.id,
						'amount': x.acount_ml_amount_id.amount,
						'acount_ml_amount_id': x.acount_ml_amount_id.id
					}

					data.append((0,0, vals))
		if data:

			self.register_payments_ids = data

			self.partner_register_ids = None
			self.onchange_move_id()



	def return_credit_aml_by_partner(self, type_partner, partner_id, amount, data_aml):
		"""
			Funcion que permite retornar el id del apunte contable asociado al pago
		"""
		domain = [('move_id', '=', self.move_id.id), ('partner_id', '=', partner_id)]

		if type_partner == False:
			domain.append(('debit', '=', 0))
			domain.append(('credit', '=', amount))
		else:
			domain.append(('debit', '!=', 0))
			domain.append(('debit', '=', amount))
		account_ml = self.env['account.move.line'].search(domain)

		print(account_ml)
		data = []
		if account_ml:
			#_logger.info('aqui')
			#_logger.info(account_ml[0].name)



			if len(account_ml) > 1:
				for x in account_ml:

					ids = []


					if x.account_id.reconcile:
						ids.extend([r.debit_move_id.id for r in x.matched_debit_ids] if x.credit > 0 else [r.credit_move_id.id for r in x.matched_credit_ids])
						ids.append(x.id)

					if len(ids) == 1:

						if x.id not in data_aml:
							
							data_aml.append(x.id)
							#move_id = account_ml[0].id
							return x.id
			else:
				ids = []


				if account_ml[0].account_id.reconcile:
					ids.extend([r.debit_move_id.id for r in account_ml[0].matched_debit_ids] if account_ml[0].credit > 0 else [r.credit_move_id.id for r in account_ml[0].matched_credit_ids])
					ids.append(account_ml[0].id)

				if len(ids) == 1:
					return account_ml[0].id

		return -1

	def payment_quick_invoice(self):
		"""
			Funcion que permite realizar el pago respectivo por cada factura
		"""

		data_partner = []

		data_aml = []

		if self.register_payments_ids:
			for x in self.register_payments_ids:
				if x.state == False:

					invoice = x.invoice_id
					credit_aml_id = x.acount_ml_amount_id.account_ml_id.id

					print('Pagando Factura: ' + str(invoice.number) + ' el credit_aml_id es: ' + str(credit_aml_id) + ' ' + str(x.amount))
					
					invoice.with_context(paid_amount=x.amount).assign_outstanding_credit(credit_aml_id)
					x.write({'state': True})
					data_aml.append(credit_aml_id)

		self.delete_amount_partner_available(data_aml)
		self.onchange_move_id()
		self.onchange_payment_partner_id()




	def validate_load_invoice_payment(self):
		"""
			Funcion que permite validar el monto a pagar
		"""
		amount = self.amount
		amount_current = self.amount_current
		amount_total = 0
		if self.partner_register_ids:
			for x in self.partner_register_ids:
				amount_total += x.amount

		if amount_total > amount_current:
			#raise Warning(_('No puede iniciar un proceso de conciliación con un valor superior al crédito. \n Si cree que esto es un error. Por favor comuniquese con el Administrador'))
			pass




AccountingEntriespaymentpartner()