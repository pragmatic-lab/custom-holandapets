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

class ProductProductInherit(models.Model):
	_inherit = "product.product"

	warehouse_quantity = fields.Char(compute='_get_warehouse_quantity', string='Ctdad Stock', store=True)
	pricelist_text = fields.Html(compute='_compute_pricelist_product_current', string='Lista de Precios')

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

	def _compute_pricelist_product_current(self):
		"""
			Funcion que permite conocer el valor del precio de lista anteriormente configurado
		"""
		for value in self:

			pricelist = ""

			product_id = self.env['product.product'].sudo().search([('id', '=', value.id)])

			if product_id:

				pricelist_ids = self.env['product.pricelist'].sudo().search([('show_price_product', '=', True)])				
			
				if pricelist_ids:

					for x in pricelist_ids:

						price_product = x.price_get(product_id.id, 1, None)

						price_unit = 0 
								
						for item in price_product:
							price_unit = price_product.get(item)

						pricelist += "* " + x.name + ": " +  str(price_unit) + '\n - '

			value.pricelist_text = str(pricelist)

			


	def _get_warehouse_quantity(self):
		"""
			Funcion que permite conocer el stock actual del producto en todos los almacenes disponibles
		"""
		for record in self:
			warehouse_quantity_text = ''
			product_id = self.env['product.product'].sudo().search([('id', '=', record.id)])
			if product_id:
				quant_ids = self.env['stock.quant'].sudo().search([('product_id','=',product_id[0].id),('location_id.usage','=','internal')])
				t_warehouses = {}
				for quant in quant_ids:
					if quant.location_id:
						if quant.location_id not in t_warehouses:
							t_warehouses.update({quant.location_id:0})
						t_warehouses[quant.location_id] += quant.quantity

				tt_warehouses = {}
				for location in t_warehouses:
					warehouse = False
					location1 = location
					while (not warehouse and location1):
						warehouse_id = self.env['stock.warehouse'].sudo().search([('lot_stock_id','=',location1.id)])
						if len(warehouse_id) > 0:
							warehouse = True
						else:
							warehouse = False
						location1 = location1.location_id
					if warehouse_id:
						if warehouse_id.name not in tt_warehouses:
							tt_warehouses.update({warehouse_id.name:0})
						tt_warehouses[warehouse_id.name] += t_warehouses[location]

				for item in tt_warehouses:
					if tt_warehouses[item] != 0:
						warehouse_quantity_text = warehouse_quantity_text + ' ** ' + item + ': ' + str(tt_warehouses[item])
		
				record.warehouse_quantity = str(warehouse_quantity_text[3:])

ProductProductInherit()