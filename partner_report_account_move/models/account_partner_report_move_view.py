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
from io import BytesIO
import base64

import time
from datetime import datetime, timedelta, date
import sys

class AccountPartnerReportMoveView(models.Model):
	_name = "account.partner_report_move_view"


	TYPE_ID = [	(1, "No identification"),
			(11, "11 - Birth Certificate"),
			(12, "12 - Identity Card"),
			(13, "13 - Citizenship Card"),
			(21, "21 - Alien Registration Card"),
			(22, "22 - Foreigner ID"),
			(31, "31 - TAX Number (NIT)"),
			(41, "41 - Passport"),
			(42, "42 - Foreign Identification Document"),
			(43, "43 - No Foreign Identification")]

	#update res_partner set first_name='acevedo',  second_name='y', first_surname='ramirez',  second_surname='jaramillo'  where id = '1934'
	partner_id = fields.Many2one('res.partner', store=True, readonly=True, copy=False, string= u'Tercero', required=True)
	#vat = fields.Char(string="Identification", store=True, readonly=True)
	#first_name = fields.Char(string="First Name", store=True, readonly=True)
	#second_name = fields.Char(string="Second Name", store=True, readonly=True)
	#first_surname = fields.Char(string="First Surname", store=True, readonly=True)
	#second_surname = fields.Char(string="Second Surname", store=True, readonly=True)
	name = fields.Char(string="Name", store=True, readonly=True)
	#doctype = fields.Selection(TYPE_ID, "Type of Identification", default=1, store=True, readonly=True)
	street = fields.Char(string="Street", store=True, readonly=True)
	#street2 = fields.Char(string="Street 2", store=True, readonly=True)
	#city_id = fields.Many2one('res.country.city', string="City", store=True, readonly=True)
	#state_id = fields.Many2one('res.country.state', string="Departamento", store=True, readonly=True)
	#country_id = fields.Many2one('res.country', string=u"País", store=True, readonly=True)

	account_id = fields.Many2one('account.account', string="Cuenta", store=True, readonly=True, copy=False, required=True)
	debit = fields.Float(string="Debito", store=True, readonly=True, copy=False)
	credit = fields.Float(string="Crédito", store=True, readonly=True, copy=False)
	balance = fields.Float(string="Balance", store=True, readonly=True, copy=False)
	account_move_id = fields.Many2one('account.move', string="Asiento Contable", store=True, readonly=True)
	account_ml_id = fields.Many2one('account.move.line', string="Apunte Contable", store=True, readonly=True)
	date = fields.Date(string="Fecha", store=True, readonly=True)
	
AccountPartnerReportMoveView()