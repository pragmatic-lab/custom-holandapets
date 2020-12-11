from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _

class PosConfig(models.Model):

    _inherit = 'pos.config'
    
    warehouse_id = fields.Many2one('stock.warehouse', u'Tienda')
    
    @api.onchange('stock_location_id',)
    def _onchange_stock_location(self):
        self.warehouse_id = self.stock_location_id.main_warehouse_id.id
