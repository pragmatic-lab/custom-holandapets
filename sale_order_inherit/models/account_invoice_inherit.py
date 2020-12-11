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
from odoo.http import request

class AccountInvoiceInherit(models.Model):

	_inherit = 'account.invoice'

	@api.model
	def _get_default_team(self):
		return self.env['crm.team']._get_default_team_id()
		
	sale_order_conf_text_id = fields.Many2one('sale.order_conf_text', string = "Configuración Reporte", track_visibility='onchange')
	payment_action_ids = fields.One2many('account.invoice_payment_action', 'invoice_id', string="Pagos", track_visibility='onchange')
	date_invoice_complete = fields.Datetime(string="Fecha Factura", default=fields.Datetime.now, track_visibility='onchange')
	#date_invoice = fields.Date(string='Invoice Date', readonly=True, states={'draft': [('readonly', False)]}, index=True, help="Keep empty to use the current date", copy=False)
	#track_visibility='onchange'
	date_invoice = fields.Date(string='Invoice Date', readonly=True, states={'draft': [('readonly', False)]}, index=True, help="Keep empty to use the current date", copy=False, track_visibility='onchange')
	date_due = fields.Date(string='Due Date', readonly=True, states={'draft': [('readonly', False)]}, index=True, copy=False,
		help="If you use payment terms, the due date will be computed automatically at the generation "
			 "of accounting entries. The Payment terms may compute several due dates, for example 50% "
			 "now and 50% in one month, but if you want to force a due date, make sure that the payment "
			 "term is not set on the invoice. If you keep the Payment terms and the due date empty, it "
			 "means direct payment.", track_visibility='onchange')
	team_id = fields.Many2one('crm.team', string='Sales Team', default=_get_default_team, oldname='section_id', track_visibility='onchange')
	#total_round = fields.Boolean(string="Redondear Totales", help="Al estar seleccionado esta opcion permite redondear los totales")



	@api.onchange('date_invoice_complete')
	def onchange_date_invoice_complete(self):
		if self.date_invoice_complete:
			self.date_invoice = str(self.date_invoice_complete)[:10]

	@api.model
	def default_get(self, default_fields):
		"""
			Funcion que nos sirve para cargar datos por defecto
				-> Impresion del reporte
				-> Lista de precios
		"""



		conf_id = self.env['sale.order_conf_text'].search([('code', '=', '12345')], limit=1)
		pricelist_id = self.env['product.pricelist'].search([('pricelist_default', '=', True)], limit=1)
		payment_term_id = self.env.ref('account.account_payment_term_immediate')

		res= super(AccountInvoiceInherit, self).default_get(default_fields)
		
		if conf_id:
			res['sale_order_conf_text_id'] = conf_id.id

		if pricelist_id:
			res['pricelist_id'] = pricelist_id.id

		return res


	def return_data_query(self, invoice_id):
		data=[]
		data_record=[]
		sql=""

		"""
			Funcion que retorna los pagos hechos en la factura
		"""

		if invoice_id:
			sql="""
					SELECT payment_id as payment_id
					FROM account_invoice_payment_rel
					WHERE invoice_id = %(invoice_id)s;
				"""%{'invoice_id': invoice_id}

			self.env.cr.execute(sql)

			res = self.env.cr.dictfetchall()

			if res:

				for x in res:
					data.append(x.get('payment_id'))
		return data


	def search_payments_invoice(self, invoice_id):

		"""
			Funcion que retorna un objeto, para mostrar informacion del pago en la impresion
		"""
		data= self.return_data_query(invoice_id)

		if data:
			payment_ids= self.env['account.payment'].search([('id', 'in', data)])

			if payment_ids:

				return payment_ids


	@api.multi
	def button_validate_stock_picking(self):

		"""
			Funcion que permite crear una factura al confirmar una venta, como tambien abrir la factura inmeditamente
		"""

		stock_picking = self.env['stock.picking'].search([('sale_id', '=', self.id)])

		return stock_picking.sudo().button_validate()


	@api.multi
	def button_open_register_payments(self):
		"""
			Funcion que permite abrir la vista de pagos
		"""

	
		context = self.env.context.copy()
		context.update( {  'ctx_invoice_id': self.id, 'ctx_partner_id': self.partner_id.id, 'ctx_currency_id': self.currency_id.id} ) 
		self.env.context = context

		return {
			'name': _('Registro de Pagos'),
			'res_model':'account.invoice_payment_action_confirm',
			'type':'ir.actions.act_window',
			'view_mode': 'form',
			'view_type': 'form',
			'target': 'new',
			'context': context
		}

	@api.multi
	def button_payment_invoice_complete(self):

		"""
			Funcion que permite hacer multiples pagos por factura, estos pagos son los que se encuentran
			en la relacion payment_action_ids, una vez pulsen el boton validar, realizará el respectivo
			pago
		"""
		data= []
		if self.payment_action_ids:

			for x in self.payment_action_ids:

				if x.amount_total > 0:
					vals = {

						'payment_type': 'inbound', 
						'partner_type': 'customer',
						'partner_id': self.partner_id.id,
						'amount': x.amount_total - x.money_back,
						'currency_id': self.currency_id.id,
						'payment_date': str(datetime.today())[0:10],
						'journal_id': x.journal_id.id,
						'communication': ' '.join([ref for ref in self.mapped('reference') if ref])[:2000],
						'payment_difference_handling': 'open',
						'writeoff_label': 'Write-Off',
						'payment_method_id': 1,
						'payment_token_id': False, 
						'partner_bank_account_id': False, 
						'writeoff_account_id': False,
						'invoice_ids': [(4, self.id, None)]
					}

					model_payment = self.env['account.payment'].create(vals)
					model_payment.action_validate_invoice_payment()

AccountInvoiceInherit()

class AccountPaymentInherit(models.Model):

	_inherit = 'account.payment'

	@api.model
	def create(self, vals):
		
		res = super(AccountPaymentInherit, self).create(vals)
		return res


AccountPaymentInherit()