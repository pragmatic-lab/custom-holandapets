# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
#                                                                             #
# Part of Odoo. See LICENSE file for full copyright and licensing details.    #
#                                                                             #
#                                                                             #
#                                                                             #
# Co-Authors    Odoo LoCo                                                     #
#               Localización funcional de Odoo para Colombia                  #
#                                                                             #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################

from odoo import models, fields, api, osv, _
import logging
_logger = logging.getLogger(__name__)
logger = logging.getLogger(__name__)
import json


class ResPartnerInherit(models.Model):

    _inherit = 'res.partner'

    @api.model
    def get_doctype(self):
        result = []

        """
        [{'id': 1, 'name': 'No identification'},
        {'id': 11, 'name': '11 - Birth Certificate'},
        {'id': 12, 'name': '12 - Identity Card'},
        {'id': 13, 'name': '13 - Citizenship Card'},
        {'id': 21, 'name': '21 - Alien Registration Card'},
        {'id': 22, 'name': '22 - Foreigner ID'},
        {'id': 31, 'name': '31 - TAX Number (NIT)'},
        {'id': 41, 'name': '41 - Passport'},
        {'id': 42, 'name': '42 - Foreign Identification Document'}, 
        {'id': 43, 'name': '43 - No Foreign Identification'}] 
        """
        for item in self.env['res.partner'].fields_get(self)['doctype']['selection']:
            description = ""
            if item[1] == 'No identification':
                description = u"Sin Identificación"
            if item[1] == '11 - Birth Certificate':
                description = u"Registro civil de nacimiento"
            if item[1] == '12 - Identity Card':
                description = u"Tarjeta de Identidad"
            if item[1] == '13 - Citizenship Card':
                description = u"Cédula de Ciudadanía"
            if item[1] == '21 - Alien Registration Card':
                description = u"Tarjeta de extranjería"
            if item[1] == '22 - Foreigner ID':
                description = u"Cédula de Extranjería"
            if item[1] == '31 - TAX Number (NIT)':
                description = u"NIT (Número de Identificación Tributaria)"
            if item[1] == '41 - Passport':
                description = u"Pasaporte"
            if item[1] == '42 - Foreign Identification Document':
                description = u"Documento de Identificación Extranjero"
            if item[1] == '43 - No Foreign Identification':
                description = u"Sin identificación del exterior o para uso definido por la DIAN"

            result.append({'id': item[0], 'name': description})

        return result 
        
    @api.model
    def create_from_ui(self, partner):

        if('doctype' in partner):
            doctype = int(partner['doctype'])
            del partner['doctype']
            partner['doctype'] = doctype

        if('personType' in partner):
            personType = int(partner['personType'])
            del partner['personType']
            partner['personType'] = personType

        partner_id = partner.pop('id', False)
        if partner_id:  # Modifying existing partner
            self.browse(partner_id).write(partner)
        else:
            partner['lang'] = self.env.user.lang
            partner_id = self.create(partner).id

        return partner_id
ResPartnerInherit()