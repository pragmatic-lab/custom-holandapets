from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class ProductPriceHistory(models.Model):
    _inherit = 'product.price.history'

    reason = fields.Char(u'Razon')
    create_date = fields.Datetime('Fecha de Creacion', readonly=True)
