from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class CommonDocumentTax(models.AbstractModel):
    _name = 'common.document.tax'
    _description = 'Plantilla para Impuestos de documentos'
    
    tax_id = fields.Many2one('account.tax', string='Impuesto')
    base = fields.Float(string='Base', digits=dp.get_precision('Account'))
    amount = fields.Float(string='Monto', digits=dp.get_precision('Account'))
