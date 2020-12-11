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

import logging
from odoo import api, fields, models, _
_logger = logging.getLogger(__name__)

import xlsxwriter
#from io import StringIO
from io import BytesIO
import base64

import time
from datetime import datetime, timedelta, date
import sys

class SummaryPaymentAccountInvoice(models.Model):
	_name = "summary.payment_account_invoice"
	_rec_name = 'partner_id'

	TYPE_JOURNAL_NAME = [ 	('card','Tarjetas'),
							('cash', 'Efectivo'),
							('transaction', u'Transación'),
							('bonus', 'Bonos'),
							('others', 'Otros') 
						]

	type_journal_name = fields.Selection(TYPE_JOURNAL_NAME, string=u"Descripción Tipo", store=True, readonly=True, copy=False)

	invoice_id = fields.Many2one('account.invoice', string="Factura",  store=True, readonly=True, copy=False)
	payment_id = fields.Many2one('account.payment', string="Pago", store=True, readonly=True, copy=False)
	type_payment = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money')], store=True, readonly=True, copy=False, string="Tipo Pago")
	number_authorization = fields.Char(store=True, readonly=True, copy=False, string=u"Número Autorización")
	move_name = fields.Char(store=True, readonly=True, copy=False, string="Asiento Contable")
	payment_name = fields.Char(store=True, readonly=True, copy=False, string="Ref. Pago")
	payment_ref = fields.Char(store=True, readonly=True, copy=False, string="Circular")
	invoice_number = fields.Char(store=True, readonly=True, copy=False, string="Factura")
	
	account_id = fields.Many2one('account.account', string="Cuenta", store=True, readonly=True, copy=False)
	account_name = fields.Char(store=True, readonly=True, copy=False, string="Nombre Cuenta")

	aml_credit = fields.Float(store=True, readonly=True, copy=False, string=u"Crédito")
	aml_debit = fields.Float(store=True, readonly=True, copy=False, string=u"Débito")
	balance = fields.Float(store=True, readonly=True, copy=False, string="Balance")

	date_move = fields.Datetime(store=True, readonly=True, copy=False, string="Fecha")
	partner_id = fields.Many2one('res.partner', store=True, readonly=True, copy=False, string= u'Cliente')
	partner_name = fields.Char(string="Nombre Partner", store=True, readonly=True, copy=False)

	journal_id = fields.Many2one('account.journal', string="Medio de Pago", store=True, readonly=True, copy=False)
	journal_name = fields.Char(string="Medio de Pago", store=True, readonly=True, copy=False)
	user_id = fields.Many2one('res.users', string="Responsable", store=True, readonly=True, copy=False)
	journal_type = fields.Selection([
			('sale', 'Sale'),
			('purchase', 'Purchase'),
			('cash', 'Dinero'),
			('bank', 'Banco'),
			('general', 'Miscellaneous'),
		], required=True, store=True, readonly=True, copy=False,
		help="Select 'Sale' for customer invoices journals.\n"\
		"Select 'Purchase' for vendor bills journals.\n"\
		"Select 'Cash' or 'Bank' for journals that are used in customer or vendor payments.\n"\
		"Select 'General' for miscellaneous operations journals.")
	type_amount = fields.Selection([('debit', 'Debito'), ('credit', u'Crédito')], string="Tipo", store=True, readonly=True, copy=False,)

SummaryPaymentAccountInvoice()