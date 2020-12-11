from odoo import models, api, fields
import odoo.addons.decimal_precision as dp


class WizardProductNoStock(models.TransientModel):
    _name = 'wizard.product.no.stock'
    _description = u'Productos sin stock'
    
    line_ids = fields.One2many('wizard.product.no.stock.detail', 'wizard_id', u'Productos sin stock')


class WizardProductNoStockDetail(models.TransientModel):
    _name = 'wizard.product.no.stock.detail'
    _description = u'Detalle de productos de producción sin stock'
    
    wizard_id = fields.Many2one('wizard.product.no.stock', u'Asistente', ondelete="cascade")
    product_id = fields.Many2one('product.product', u'Producto')
    product_qty = fields.Float(u'Cantidad Requerida', digits=dp.get_precision('Product Unit of Measure'))
    qty_available = fields.Float(u'Cantidad Disponible', digits=dp.get_precision('Product Unit of Measure'))
    uom_id = fields.Many2one('uom.uom', u'UdM')
    location_id = fields.Many2one('stock.location', u'Bodega')
    lot_id = fields.Many2one('stock.production.lot', u'Lote de Producción')
