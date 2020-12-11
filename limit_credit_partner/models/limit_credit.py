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

class LimitCredit(models.Model):

	_name = 'limit.credit'

	def _get_credit_limit_partner(self):

		if self.partner_id:

			model_credit_limit_partner = self.env['limit.credit_partner']

			return model_credit_limit_partner.search([('partner_id', '=', self.partner_id.id)])




	name = fields.Char(string= u"Código", store=True, readonly=True)
	partner_id = fields.Many2one("res.partner", string= u"Cliente", store=True, readonly=True)
	credit = fields.Float(string= u"Crédito", store=True, readonly=True)	
	limit_credit_partner_ids = fields.Many2many('limit.credit_partner', 'limit_credit_partner_rel', column1='limit_credit_partner_id', column2='limit_credit_id',  String= u"Histórico", compute= '_compute_credit_limit_partner')
	registration_day = fields.Datetime('Date current action', select=True , default=lambda self: fields.datetime.now(), store=True, readonly=True)


	@api.multi
	def _compute_credit_limit_partner(self):
		if self.partner_id:

			model_credit_limit_partner = self.env['limit.credit_partner']

			model_credit_limit_partner_ids = model_credit_limit_partner.search([('partner_id', '=', self.partner_id.id)])

			data = []
			aux = []
			for x in model_credit_limit_partner_ids:
				aux.append(x.id)
			data = [(6,0,aux)]

			self.limit_credit_partner_ids = data



	@api.model
	def create(self, vals):

		vals['name'] = self.env['ir.sequence'].next_by_code('credit.limit_partner')
		res = super(LimitCredit, self).create(vals)
		return res


	def vals_limit_credit(self, partner_id, credit):
		
		vals= {
		'partner_id': partner_id,
		'credit': credit,
		}

		return vals


	def create_limite_credit(self, partner_id, credit):
		"""
			Función que permite crear un registro del movimiento del crédito del partner
		"""
		if partner_id:
		
			self.create(self.vals_limit_credit(partner_id, credit))


	def search_partner(self, partner_id):

		if partner_id:
			if len(self.search([('partner_id', '=', partner_id)])) > 0:
				return True

		return False



LimitCredit()