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

class TaxesCollected(models.Model):

	_name = 'taxes.collected'

	name = fields.Many2one('taxes.collected_name', string= u"Descripción")
	type_taxes = fields.Selection([('tax_client', 'Impuesto Cliente'), ('tax_company', 'Impuesto Empresa')], string="A cargo de")
	account_id = fields.Many2one('account.account', string="Cuenta")

	_sql_constraints = [('taxes_collected_name_uniq', 'unique (name)', u'La Descripción debería ser unica')]

TaxesCollected()