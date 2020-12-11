from odoo import models, api, fields


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'
    
    def _rename_location(self, location, name):
        location.write({'name': name})
    
    @api.multi
    def _update_name_and_code(self, new_name=False, new_code=False):
        res = super(StockWarehouse, self)._update_name_and_code(new_name, new_code)
        if new_name:
            self.mapped('lot_stock_id').mapped('location_id').write({'name': new_name})
        else:
            for warehouse in self:
                if self.lot_stock_id.location_id:
                    self.lot_stock_id.location_id.write({'name': warehouse.name})
        return res
    
    @api.model
    def create(self, vals):
        new_rec = super(StockWarehouse, self).create(vals)
        #a la bodega tipo vista no usar nombre corto del almacen, usan el nombre completo del almacen
        if new_rec.lot_stock_id.location_id:
            self._rename_location(new_rec.lot_stock_id.location_id, new_rec.name)
        return new_rec
