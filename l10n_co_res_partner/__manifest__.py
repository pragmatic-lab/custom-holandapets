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

{
    'name': 'Terceros - Colombia',
    'category': 'Localization',
    'version': '12.0',
    'author': 'Odoo LoCo',
    'license': 'AGPL-3',
    'maintainer': 'Odoo LoCo',
    'website': 'https://github.com/odooloco',
    'summary': 'Terceros Colombia: Extendido de Partner / '
               'Modulo de Contactos - Odoo 12.0',
    'images': ['images/main_screenshot.png'],
    'depends': [
    'base',
    'l10n_co',
    'account'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/ciiu.xml',
        'data/l10n_cities_co_data.xml',
        'data/res.ciiu.csv',
        'views/l10n_co_res_partner.xml',
        'views/auth_signup_inherit.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
