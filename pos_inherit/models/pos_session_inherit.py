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

class PosSessionInherit(models.Model):
	_inherit = "pos.session"



	def return_payment_orders(self, session_id):

		amount_base = 0
		amount_tax = 0
		amount_total = 0
		amount_discount = 0
		amount_refund = 0
		amount_cash = 0
		amount_bank = 0

		if session_id:
			order_ids = self.env['pos.order'].search([('session_id', '=', session_id)])




			if order_ids:


				for x in order_ids:

					if x.statement_ids:
						for value in x.statement_ids:
							if value.journal_id.type == 'cash':
								amount_cash += value.amount
							if value.journal_id.type == 'bank':
								amount_bank += value.amount
					amount_tax += x.amount_tax
					amount_base += (x.amount_total - x.amount_tax)
					amount_total += x.amount_total

					if x.lines:
						for value in x.lines:
				
							amount_discount += ((value.qty * value.price_unit) - value.price_subtotal)
							if value.qty < 0:

								amount_refund += value.price_subtotal_incl

		return {
			'amount_total': amount_total,
			'amount_tax': amount_tax,
			'amount_base': amount_base,
			'amount_discount': amount_discount,
			'amount_refund': amount_refund,
			'amount_cash': amount_cash,
			'amount_bank': amount_bank,
		}

PosSessionInherit()


