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

class VendorCommissionConf(models.Model):

	_name = 'commission.vendor.conf'

	def get_days():
		day_list = []

		for i in range(0, 92):
			day_list.append((str(i), (str(i) + ' dias') ))
		day_list.append(('hundred_more', 'Mayor que 100' ))
		return day_list

	commision_vendor_id = fields.Many2one('commision_vendor_id', string="Commission Report")
	commision_vendor_master_id = fields.Many2one('commision_vendor_id', string="Commission Master")
	#name = fields.Char(string=u"Descripción", required=True)
	day_begin = fields.Selection(get_days(), string='De', required=True)
	day_end = fields.Selection(get_days(), string='A', required=True)
	value_commission = fields.Float(string=u"Comisión", required=True)
	
VendorCommissionConf()