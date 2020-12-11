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

class SaleOrderInherit(models.Model):

	_inherit = 'sale.order'


	def validate_create_quick_invoice(self):
		"""
			Funcion que permite validar si se puede crear o no la factura rapida
		"""
		if self.env.user.has_group('sale_quick.group_create_invoice_quick_configuration'):
			return  True
		
		return False


	@api.multi
	def button_quick_create_invoice_complete(self):
		"""
			Funcion que permite crear una factura al confirmar una venta, confirmar el stock picking y abrir la factura inmeditamente
		"""
		if self.validate_create_quick_invoice():
			imediate_obj=self.env['stock.immediate.transfer']
			for order in self:

				order.action_confirm()

				warehouse=order.warehouse_id

				for picking in self.picking_ids:
					picking.action_confirm()
					picking.action_assign()


					imediate_rec = imediate_obj.create({'pick_ids': [(4, order.picking_ids.id)]})
					imediate_rec.process()
					if picking.state !='done':
						for move in picking.move_ids_without_package:
							move.quantity_done = move.product_uom_qty
						picking.button_validate()

				self._cr.commit()

				order.action_invoice_create()  

				return order.action_view_invoice()


	@api.multi
	def button_quick_create_invoice(self):
		"""
			Funcion que permite crear una factura al confirmar una venta, como tambien abrir la factura inmeditamente, pero sin confirmar el stock picking
		"""
		if self.validate_create_quick_invoice():
			for order in self:
				order.action_confirm()			
				order.action_invoice_create()  

				return order.action_view_invoice()


SaleOrderInherit()