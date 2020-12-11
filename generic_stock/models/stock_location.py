from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class StockLocation(models.Model):
    _inherit = 'stock.location'
    
    main_warehouse_id = fields.Many2one('stock.warehouse', 'Almacen', compute='_compute_warehouse')
    
    @api.depends()
    def _compute_warehouse(self):
        for location in self:
            domain_warehouse = [
                '|', 
                ('view_location_id', '=', location.id),
                ('lot_stock_id', '=', location.id),
            ]
            location.main_warehouse_id = self.env['stock.warehouse'].search(domain_warehouse, limit=1)