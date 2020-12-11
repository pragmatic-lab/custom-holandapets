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

import re
from datetime import datetime, timedelta, date

import xlsxwriter
from io import BytesIO
import base64

from odoo import api, fields, models, _

from odoo.exceptions import UserError
from odoo.tools import pycompat
from odoo.tools.translate import _

import sys


class ReportCertificationsIva(models.TransientModel):
	_name = 'report.certification_iva'
	_description = "Colombian Certification Report IVA"
	_inherit = 'report.certification_base'

	partner_ids = fields.Many2many(comodel_name='res.partner', relation='report_certification_iva_partner_rel', column1='report_id', column2='partner_id', string='Terceros')

	def _get_report_name(self):
		return u'Retención en IVA'

	def _get_columns_name(self):
		return [
			{'name': 'Nombre'},
			{'name': 'Bimestre'},
			{'name': u'Monto Total Operación', 'class': 'number'},
			{'name': u'Monto del Pago Sujeto Retención', 'class': 'number'},
			{'name': 'Retenido Consignado', 'class': 'number'},
			{'name': '%', 'class': 'number'},
		]

	def _get_values_for_columns(self, values):
		return [{'name': values['name'], 'field_name': 'name'},
				{'name': self.format_value(values['tax_base_amount']), 'field_name': 'tax_base_amount'},
				{'name': self.format_value(values['balance_15_over_19']), 'field_name': 'balance_15_over_19'},
				{'name': self.format_value(values['balance']), 'field_name': 'balance'},
				{'name': 0.15 if values['balance'] else 0, 'field_name': 'percentage'}]

	def _get_domain(self):
		res = super(ReportCertificationsIva, self)._get_domain()

		if self.partner_ids:
			res += ['|', ('account_id.code', '=', '236705'), ('account_id.code', '=like', '240810%'), ('partner_id', 'in', [x.id for x in self.partner_ids])]
		else:
			res += ['|', ('account_id.code', '=', '236705'), ('account_id.code', '=like', '240810%')]

		return res

	def _handle_aml(self, aml, lines_per_bimonth):
		bimonth = self._get_bimonth_for_aml(aml)
		if bimonth not in lines_per_bimonth:
			lines_per_bimonth[bimonth] = {
				'name': self._get_bimonth_name(bimonth),
				'tax_base_amount': 0,
				'balance': 0,
				'balance_15_over_19': 0,
			}

		if aml.account_id.code.startswith('240810'):
			lines_per_bimonth[bimonth]['balance_15_over_19'] += aml.credit - aml.debit
		else:
			lines_per_bimonth[bimonth]['balance'] += aml.credit - aml.debit
			if aml.credit:
				lines_per_bimonth[bimonth]['tax_base_amount'] += aml.tax_base_amount
			else:
				lines_per_bimonth[bimonth]['tax_base_amount'] -= aml.tax_base_amount



	def return_excel(self):
		"""
			Funcion que permite retornar la vista para descargar el excel
		"""
		return {
			'name': _(u'Certificado de Retención en IVA'),
			'res_model':'report.certification_iva',
			'type':'ir.actions.act_window',
			'view_type':'form',
			'view_mode':'form',
			'target':'new',
			'nodestroy': True,
			'res_id': self.id
		}


ReportCertificationsIva()