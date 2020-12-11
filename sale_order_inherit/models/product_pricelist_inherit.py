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
from dateutil.relativedelta import *
import logging
_logger = logging.getLogger(__name__)
from odoo import modules
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError

class ProductPriceListInherit(models.Model):

	_inherit = 'product.pricelist'

	pricelist_default = fields.Boolean(string="Precio de Lista en Ventas", default=False)
	show_price_product = fields.Boolean(string="Mostrar en Producto", default=False)

	def return_message(self, record):

		msg = _( 'Solamente se puede configurar una Lista de Precios por defecto ' +  '\n La Lista de precios actual es: ' + str(record[0].name))
		raise ValidationError(msg)


	def validation_default_pricelist(self, vals):

		if 'pricelist_default' in vals:

			if vals['pricelist_default']:
				record= self.search([('pricelist_default', '=', True)])
				if len(record) > 0:
					self.return_message(record)


	@api.model
	def create(self, vals):

		self.validation_default_pricelist(vals)
		res = super(ProductPriceListInherit, self).create(vals)
		
		return res

	@api.multi
	def write(self, vals):

		self.validation_default_pricelist(vals)
		res= super(ProductPriceListInherit,self).write(vals)

		return res

ProductPriceListInherit()
