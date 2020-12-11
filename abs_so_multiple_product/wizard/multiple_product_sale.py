# -*- coding: utf-8 -*-
#################################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2019-today Ascetic Business Solution <www.asceticbs.com>
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
from odoo import api, fields, models,_

#create a new class for MultipleProductSale. 
class MultipleProductSale(models.TransientModel):
    _name = "multiple.product.sale"
 
    product_ids = fields.Many2many('product.product',string='Products')

    def add_multiple_product_sale(self):
        order_line_object = self.env['sale.order.line']  
        if self.env.context.get('active_model')=='sale.order': 
            active_id = self.env.context.get('active_id',False)
            order_id = self.env['sale.order'].search([('id', '=', active_id)]) 
            if order_id and self.product_ids:    
                for record in self.product_ids:
                    if record:      
                        order_line_dict ={
                                  'order_id':order_id.id,
                                  'product_id':record.id,
                                  }          
                        order_line_object.create(order_line_dict)
