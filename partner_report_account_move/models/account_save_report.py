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

import logging
from odoo import api, fields, models, _
_logger = logging.getLogger(__name__)


class AccountSaveReport(models.Model):
	_name = "account.save_report"

	name = fields.Char(string= u'Descripción', required=True)
	account_ids = fields.Many2many('account.account', 'report_account_ids_save_report_rel', column1='save_report_id', column2="account_id", string="Cuentas", required=True)

	_sql_constraints = [('account_save_report_name_uniq', 'unique (name)', 'El nombre debe ser unico')]

AccountSaveReport()