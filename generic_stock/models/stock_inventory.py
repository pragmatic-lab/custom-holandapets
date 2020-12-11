from odoo import models, api, fields, tools
from odoo.exceptions import UserError, ValidationError
import odoo.addons.decimal_precision as dp


class StockInventory(models.Model):
    _inherit = ['mail.thread', 'stock.inventory']
    _name = 'stock.inventory'
    
    # reemplazar campos para agregar track_visibility
    state = fields.Selection(track_visibility='onchage')
    location_id = fields.Many2one('stock.location', track_visibility='onchage')
    
    @api.multi
    def unlink(self):
        for inventory in self:
            if inventory.state not in ('draft', 'cancel'):
                raise UserError("No puede eliminar el ajuste de inventario, intente cancelarlo primero")
        return super(StockInventory, self).unlink()

    @api.multi
    def _get_inventory_lines_values(self):
        product_model = self.env['product.product']
        values = super(StockInventory, self)._get_inventory_lines_values()
        for val in values:
            if val.get('product_id'):
                product = product_model.browse(val['product_id'])
                val.update({'price_unit': product.standard_price})
        return values

    
class StockInventoryLine(models.Model):
    _inherit = 'stock.inventory.line'
    
    price_unit = fields.Float('Precio Unitario', 
        digits=dp.get_precision('Product Price'), group_operator="avg")
    
    @api.onchange('product_id')
    def _onchange_product(self):
        res = super(StockInventoryLine, self)._onchange_product()
        if self.product_id:
            self.price_unit = self.product_id.standard_price
        return res
    
    @api.onchange('product_id', 'location_id', 'product_uom_id', 'prod_lot_id', 'partner_id', 'package_id')
    def _onchange_quantity_context(self):
        if self.product_id and self.product_id.uom_id.category_id == self.product_uom_id.category_id:
            self.price_unit = self.product_id.uom_id._compute_price(self.product_id.standard_price, self.product_uom_id)
        return super(StockInventoryLine, self)._onchange_quantity_context()
    
    def _get_move_values(self, qty, location_id, location_dest_id, out):
        vals = super(StockInventoryLine, self)._get_move_values(qty, location_id, location_dest_id, out)
        vals['price_unit'] = self.price_unit
        return vals
