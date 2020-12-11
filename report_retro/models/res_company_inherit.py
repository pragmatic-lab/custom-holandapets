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

class ResCompanyInherit(models.Model):

	_inherit = "res.company"

	@api.model
	def update_compnay_data(self):
		"""
			Función que permite actualizar el footer y el encabezado en los reportes
		"""

		company = self.env.user.company_id
		company_id = company.id
		report_footer = company.report_footer

		external_report_layout_id = self.env['ir.ui.view'].search([('name', '=', 'external_layout_retro')]).id
		report_paperformat_id = self.env['report.paperformat'].search([('name', '=', 'Carta Col')]).id
		


		self.search([('id', '=', company_id)]).write({'report_footer': u"Efectuar pago a nombre de SYSCORD SAS en nuestras cuentas bancarias \n" + 
				u"Davivienda cuenta de ahorros 019170025167 \n" + 
				u"Bancolombia cuenta corriente 75072995790 \n" + 
				u"Actividad económica ICA 305 (6.6 por mil)\n" + 
				"Factura impresa por Syscord", 'report_header': "Integrando Soluciones", 'external_report_layout_id': external_report_layout_id, 'paperformat_id': report_paperformat_id})


ResCompanyInherit()