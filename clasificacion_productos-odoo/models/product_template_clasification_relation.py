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

class ProductTemplateClasificationRelation(models.Model):

	_name = 'product.template_clasification_relation'
	_rec_name = 'product_template_clasification_id'

	_description = "Product Template Clasification"


	product_template_clasification_id = fields.Many2one('product.template_clasification', String= u"Clasificación")
	product_template_clasification_line_ids = fields.Many2many('product.template_clasification_line', 'product_template_clasification_line_rel', column1='product_template_clasification_relation_id', column2='product_template_clasification_line_id',  String= u"Atributos de Clasificación")
	line_clasification_text = fields.Char(String= u"Atributos de Clasificación", compute='_update_line_clasification')

	@api.one
	def _update_line_clasification(self):
		return_line = ""
		if self.product_template_clasification_line_ids:
			for x in self.product_template_clasification_line_ids:
				return_line += x.name + " - "

		if len(return_line) == 0:
			self.line_clasification_text = "No hay registros"
		else:
			self.line_clasification_text = return_line[0:len(return_line)-2]

ProductTemplateClasificationRelation()