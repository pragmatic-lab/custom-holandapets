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


class ReportCertificationsPartner(models.TransientModel):
	_name = 'report.certification_partner'
	_description = "Colombian Certification Report Partner"
	_inherit = 'report.certification_base'

	partner_ids = fields.Many2many(comodel_name='res.partner', relation='report_certification_fuente_partner_rel', column1='report_id', column2='partner_id', string='Terceros')


	def _get_report_name(self):
		return u'Retención por Terceros'

	def _get_columns_name(self):
		return [
			{'name': u'Nombre'},
			{'name': u'Concepto de retención'},
			{'name': u'Monto del Pago Sujeto Retención', 'class': 'number'},
			{'name': u'Retenido Consignado', 'class': 'number'},
		]

	def _get_values_for_columns(self, values):
		return [{'name': values['name'], 'field_name': 'name'},
				{'name': self.format_value(values['tax_base_amount']), 'field_name': 'tax_base_amount'},
				{'name': self.format_value(values['balance']), 'field_name': 'balance'}]

	def _get_domain(self):
		res = super(ReportCertificationsPartner, self)._get_domain()
		if self.partner_ids:
			res += [('account_id.code', '=like', '2365%'), ('account_id.code', '!=', '236505'), ('partner_id', 'in', [x.id for x in self.partner_ids])]
		else:
			res += [('account_id.code', '=like', '2365%'), ('account_id.code', '!=', '236505')]
		return res

	def _handle_aml(self, aml, lines_per_account):
		account_code = aml.account_id.code
		if account_code not in lines_per_account:
			lines_per_account[account_code] = {
				'name': aml.account_id.display_name,
				'tax_base_amount': 0,
				'balance': 0,
			}

		lines_per_account[account_code]['balance'] += aml.credit - aml.debit
		if aml.credit:
			lines_per_account[account_code]['tax_base_amount'] += aml.tax_base_amount
		else:
			lines_per_account[account_code]['tax_base_amount'] -= aml.tax_base_amount

	def return_excel(self):
		"""
			Funcion que permite retornar la vista para descargar el excel
		"""
		return {
			'name': _(u'Certificado de Retención de Terceros'),
			'res_model':'report.certification_partner',
			'type':'ir.actions.act_window',
			'view_type':'form',
			'view_mode':'form',
			'target':'new',
			'nodestroy': True,
			'res_id': self.id
		}

ReportCertificationsPartner()