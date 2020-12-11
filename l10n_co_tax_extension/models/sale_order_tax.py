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
from odoo.addons import decimal_precision as dp

class SaleOrderTax(models.Model):
	_name = 'sale.order.tax'
	_order = 'sequence'

	order_id = fields.Many2one('sale.order',string='Sale Order', ondelete='cascade')
	tax_id = fields.Many2one('account.tax', string='Impuesto')
	name = fields.Char(string=u'Descripción Impuesto', required=True)
	base = fields.Float(string='Base', digits=dp.get_precision('Product Unit of Measure'))
	amount = fields.Float(string='Amount', digits=dp.get_precision('Product Unit of Measure'))
	sequence = fields.Integer(string='Sequence',help="Gives the sequence order when displaying a list of order tax.")

SaleOrderTax()