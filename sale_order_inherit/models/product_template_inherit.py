# -*- coding: utf-8 -*-
#################################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2017-Today Ascetic Business Solution <www.asceticbs.com>
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
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#################################################################################

from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)

class ProductTemplateInherit(models.Model):
	_inherit = "product.template"

	item = fields.Char(string="Item", readonly=True, store=True)
	
	@api.model
	def create(self, vals):
		vals['item'] = self.env['ir.sequence'].next_by_code('product.template_item')
		res = super(ProductTemplateInherit, self).create(vals)
		return res

	@api.multi
	def update_field_item_product(self):
		"""
			Funcion que permite actualizar de forma automatica el item de todos los productos hasta el momento
		"""
		product_ids = self.search([], order='name asc')

		if product_ids:
			for x in product_ids:
				x.write({'item': self.env['ir.sequence'].next_by_code('product.template_item')})


	@api.model
	def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
		args = args or []
		_logger.info('entramos')
		_logger.info(name)
		if name:
				#name = name.split(' - ')[-1]
				args = ['|', '|', '|', ('name', operator, name), ('barcode', operator, name), ('item', operator, name), ('default_code', operator, name)] + args
		product_ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
		return self.browse(product_ids).name_get()
		#super(ResPartnerInherit, self)._name_search(name, args, operator=operator, limit=limit, name_get_uid=name_get_uid)

ProductTemplateInherit()