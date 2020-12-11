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

from odoo import models, fields, api, _
import logging

class ReporteKardexLines(models.Model):
	_name = 'report.kardex.lines'


	date_begin = fields.Datetime(string="Fecha Inicial")
	date_end = fields.Datetime(string="Fecha Final")
	

	ubicacion_id = fields.Many2one("stock.location", string="Ubicacion")
	product_id = fields.Many2one("product.product", string="Productos")

	date_move = fields.Datetime(string="Fecha")
	document = fields.Char(string='Documento')
	partner_id = fields.Many2one('res.partner', String="Empresa")
	type_move = fields.Char(string='Tipo')
	#uom_id = fields.Binary(related='product_id.uom_id', string=u"Unidades")
	inventory_initial = fields.Float(string='Inicial')
	inventory_in = fields.Float(string='Entradas')
	inventory_out = fields.Float(string='Salidas')
	inventory_final = fields.Float(string='Final')
	standard_price = fields.Float(string='Costo')
	total_inventory = fields.Float(string='Total')
	inventory_move_in = fields.Float(string='Entrada')
	inventory_move_out = fields.Float(string='Salida')
	inventory_saldo = fields.Float(string='Saldo')
	total = fields.Float(string='Total')

ReporteKardexLines()