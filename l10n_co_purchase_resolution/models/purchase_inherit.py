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

class PurchaseInherit(models.Model):

	_inherit = 'purchase.order'

	resolution_number = fields.Char('Resolution number in invoice')
	resolution_date = fields.Date()
	resolution_date_to = fields.Date()
	resolution_number_from = fields.Integer("")
	resolution_number_to = fields.Integer("")

	@api.multi
	def button_confirm(self):
		result = super(PurchaseInherit, self).button_confirm()

		for inv in self:
			sequence_id = self.env['ir.sequence'].search([('code', '=', 'purchase.order')])
			if sequence_id:
				sequence = self.env['ir.sequence.dian_resolution'].search([('sequence_id','=',sequence_id.id),('active_resolution','=',True)], limit=1)
				inv.resolution_number = sequence['resolution_number']
				inv.resolution_date = sequence['date_from']
				inv.resolution_date_to = sequence['date_to']
				inv.resolution_number_from = sequence['number_from']
				inv.resolution_number_to = sequence['number_to']
		return result


PurchaseInherit()