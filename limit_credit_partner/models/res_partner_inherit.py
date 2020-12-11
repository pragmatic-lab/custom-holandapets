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
import threading
from odoo.osv import osv

class ResPartnerInherit(models.Model):

	_inherit = 'res.partner'

	verificate_credit = fields.Boolean(string= u"Verificar Crédito")
	limit_credit = fields.Float(string= u"Límite Crédito")
	block_credit = fields.Boolean(string= u"Bloquear Crédito")
	avaliable_credit = fields.Float(string= u"Crédito", compute = '_compute_calculate_credit_partner')
	avaliable_debit = fields.Float(string= u"Dédito", compute = '_compute_calculate_debit_partner')



	@api.one
	def _compute_calculate_credit_partner(self):
		if self.limit_credit:

			model_credit_limit_partner = self.env['limit.credit_partner']

			credit_partner_id = model_credit_limit_partner.search([('partner_id', '=', self.id)], limit= 1, order= 'registration_day desc')

			self.avaliable_credit = credit_partner_id.credit


	@api.one
	def _compute_calculate_debit_partner(self):
		if self.limit_credit:

			model_credit_limit_partner = self.env['limit.credit_partner']

			credit_partner_id = model_credit_limit_partner.search([('partner_id', '=', self.id)], limit= 1, order= 'registration_day desc')

			self.avaliable_debit = credit_partner_id.debit



	@api.onchange('verificate_credit')
	def onchange_verificate_credit(self):
		if self.verificate_credit:
			self.limit_credit = 0
		else:
			self.limit_credit = 0


	def know_blocking(self, partner):
		
		"""
			Función que permite saber si el cliente esta bloqueado o no para poder realizar ordenes de venta
		"""

		if partner:
			if partner.block_credit:
				raise osv.except_osv(_('Alerta!'), _('El cliente %s, esta bloqueado temporalmente. \n Por favor comunicarse con el Administrador') % self.partner_id.name)


	@api.model
	def create(self, vals):

		model_credit_limit_partner = self.env['limit.credit_partner']
		model_credit_limit = self.env['limit.credit']


			
		res = super(ResPartnerInherit, self).create(vals)

		if vals.get('limit_credit'):

			if self.limit_credit > 0:

				model_credit_limit_partner.create_limite_credit(res.id, res.limit_credit, 0, None, 0, None)
				model_credit_limit.create_limite_credit(res.id, res.limit_credit)

		return res

	@api.multi
	
	def write(self, vals):

		model_credit_limit_partner = self.env['limit.credit_partner']
		model_credit_limit = self.env['limit.credit']

		if vals.get('limit_credit') and vals.get('verificate_credit'):

			if vals.get('limit_credit') > 0:

				if vals.get('verificate_credit') or self.verificate_credit:

					credit_previous= 0
					credit_now = vals.get('limit_credit')

					if self.limit_credit == False:
						credit_previous=0
					else:
						credit_previous = self.limit_credit

					result_credit = credit_now - credit_previous

					if (result_credit) != 0 and result_credit != credit_now:

						credit_partner_id = model_credit_limit_partner.search([('partner_id', '=', self.id)], limit= 1, order= 'registration_day desc')
						limit_credit = model_credit_limit.search([('partner_id', '=', self.id)], limit= 1, order= 'registration_day desc')
						
						if credit_partner_id:
							_logger.info('vamos a editar')
							if result_credit < 0:
								#vamos a restar credito
								_logger.info('vamos a restar el credito')
								if result_credit <= credit_partner_id.credit:
									#si puede restar el credito
									_logger.info('si se pudo editar')
									credit_partner_id.write({'credit': credit_partner_id.credit + result_credit})
									limit_credit.write({'credit': limit_credit.credit + result_credit})
								else:
									_logger.info('no se pudo restar el credito')
									raise osv.except_osv(_(u'Alerta Crédito!'), _('El cliente %s, tiene un crédito de %s , por que no se puede reducir su crédito. \n Para poder reducir el crédito debe realizar un pago mayor o igual a %s') %(self.partner_id.name, credit_partner_id.credit, -result_credit))

							else:
								#vamos a aumentar credito
								_logger.info('vamos a aumentar')
								credit_partner_id.write({'credit': credit_partner_id.credit + result_credit})
								limit_credit.write({'credit': limit_credit.credit + result_credit})

						elif limit_credit:
							_logger.info('vamos a editarsdsdsd')
							if result_credit < 0:
								#vamos a restar credito
								_logger.info('vamos a restar el credito')
								if result_credit <= limit_credit.credit:
									#si puede restar el credito
									_logger.info('si se pudo editar')
									limit_credit.write({'credit': limit_credit.credit + result_credit})
								else:
									_logger.info('no se pudo restar el credito')
									raise osv.except_osv(_(u'Alerta Crédito!'), _('El cliente %s, tiene un crédito de %s , por que no se puede reducir su crédito. \n Para poder reducir el crédito debe realizar un pago mayor o igual a %s') %(self.partner_id.name, limit_credit.credit, -result_credit))

							else:
								#vamos a aumentar credito
								_logger.info('vamos a aumentar')
								limit_credit.write({'credit': limit_credit.credit + result_credit})
						else:
							model_credit_limit_partner.create_limite_credit(self.id, vals.get('limit_credit'), 0, None, 0, None)

					else:
						model_credit_limit_partner.create_limite_credit(self.id, vals.get('limit_credit'), 0, None, 0, None)

		res = super(ResPartnerInherit, self).write(vals)

		if vals.get('limit_credit'):
			if model_credit_limit.search_partner(self.id) == False:
				model_credit_limit.create_limite_credit(self.id, vals.get('limit_credit'))


		return res

ResPartnerInherit()