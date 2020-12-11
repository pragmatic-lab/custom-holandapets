from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'
    
    @api.onchange('code')
    def onchange_picking_code(self):
        #establecer los valores correctos para la creacion de lotes
        if self.code == 'incoming':
            self.use_create_lots = True
            self.use_existing_lots = False
        else:
            self.use_create_lots = False
            self.use_existing_lots = True
        return super(StockPickingType, self).onchange_picking_code()
