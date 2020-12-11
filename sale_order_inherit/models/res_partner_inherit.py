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


import json
from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError, ValidationError

ADDRESS_FORMAT_CLASSES = {
	'%(state_code)s': 'o_city_state',

}

ADDRESS_FIELDS = ('street', 'street2', 'state_id', 'country_id')

"""
class format_address(object):

	@api.model
	def fields_view_get_address(self, arch):
		address_format = self.env.user.company_id.country_id.address_format or ''
		for format_pattern, format_class in ADDRESS_FORMAT_CLASSES.iteritems():
			if format_pattern in address_format:
				doc = etree.fromstring(arch)
				for address_node in doc.xpath("//div[@class='o_address_format']"):
					# add address format class to address block
					address_node.attrib['class'] += ' ' + format_class
					if format_class.startswith('o_zip'):
						zip_fields = address_node.xpath("//field[@name='zip']")
						city_fields = address_node.xpath("//field[@name='city']")
						if zip_fields and city_fields:
							# move zip field before city field
							city_fields[0].addprevious(zip_fields[0])
				arch = etree.tostring(doc)
				break
		return arch


"""


class ResPartnerInherit(models.Model):

	_inherit = 'res.partner'

	neighborhood = fields.Char(string="Barrio")
	box_id = fields.Many2one('sale.order_conf_box', string="Caja")
	percentage_price = fields.Float(string='Procentaje en el Precio (%)',)


	@api.model
	def create(self, vals):

		print(self)
		print(vals)

		if 'doctype' in vals:

			if vals['doctype'] == 1:
				if vals['customer']:
					raise ValidationError(u"El contacto que esta creando debe tener un tipo de identificación valido")

		res = super(ResPartnerInherit, self).create(vals)

		return res

	@api.multi
	def write(self, vals):

		if 'doctype' in vals:

			if vals['doctype'] == 1:
				if self.customer:

					raise ValidationError(u"El contacto que esta editando debe tener un tipo de identificación valido")

		res = super(ResPartnerInherit, self).write(vals)

		return res


	@api.model
	def _address_fields(self):
		"""Returns the list of address fields that are synced from the parent."""
		return list(ADDRESS_FIELDS)


	def _display_address(self, without_company=False):

		"""
			Funcion que permite agregar campos al widget del contacto
		"""
		address_format = self._get_address_format()
		address_format += "%(neighborhood)s\n %(mobile)s\n %(phone)s\n"

		val_city = ""
		if self.city:
			val_city = 'Ciudad: ' + str(self.city)
			
		val_neighborhood = ""
		if self.neighborhood:
			val_neighborhood = 'Barrio: ' + str(self.neighborhood)

		val_street2 = ""
		if self.street2:
			val_street2 = u'Otra Dirección: ' + str(self.street2)

		val_mobile = ""
		if self.mobile:
			val_mobile = u'Teléfono: ' + str(self.mobile)

		val_phone = ""
		if self.phone:
			val_phone = u'Celular: ' + str(self.phone)

		args = {
			'state_code':  '',
			'state_name':  '',
			'country_code':  '',
			'city': val_city,
			'zip':'',
			'street2': val_street2,
			'country_name': '',
			'company_name': self.commercial_company_name or '',
			'neighborhood': val_neighborhood,
			'phone': val_mobile,
			'mobile': val_phone
		}
		for field in self._address_fields():
			args[field] = getattr(self, field) or ''
		if without_company:
			args['company_name'] = ''
		# elif address.parent_id:
		# 	address_format = '%(company_name)s\n' + address_format
		return address_format % args

	@api.model
	def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
		args = args or []
		_logger.info('entramos')
		_logger.info(name)
		if name:
				#name = name.split(' - ')[-1]
				args = ['|', ('name', operator, name), ('xidentification', operator, name)] + args
		partner_ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
		return self.browse(partner_ids).name_get()
		#super(ResPartnerInherit, self)._name_search(name, args, operator=operator, limit=limit, name_get_uid=name_get_uid)

	"""
	@api.multi
	def name_get(self):
		res = []
		for record in self:
			name = record.name
			if record.xidentification:
				name = u"%s - %s" % (record.xidentification, name)
			res.append((record.id, name))
		return res
	"""
		
ResPartnerInherit()