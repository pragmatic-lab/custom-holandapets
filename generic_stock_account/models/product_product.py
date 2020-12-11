from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    @api.onchange('categ_id')
    def onchange_product_categ(self):
        #cuando se cambia la categoria de producto
        #si la cuenta contable de la categoria anterior es diferente a la cuenta contable de la nueva categoria
        #y ese producto tiene stock, no permitir cambiar de categoria, 
        #se deberia usar un asistente para realizar ese cambio de categoria
        if self.categ_id and self._origin and self.categ_id.property_stock_valuation_account_id != self._origin.categ_id.property_stock_valuation_account_id:
            if self.qty_available > 0:
                self.categ_id = self._origin.categ_id.id
                warning = {'title': 'Advertencia',
                           'message': 'No puede cambiar la categoria del producto, ya que hay stock y su contabilidad podria verse afectada.\n ' \
                                        'Use el asistente para Cambiar de Categoria a los productos'
                           }
                return {'warning': warning}
    
    @api.model
    def _anglo_saxon_sale_move_lines(self, name, product, uom, qty, price_unit, currency=False, amount_currency=False, fiscal_position=False, account_analytic=False, analytic_tags=False):
        if self.env.context.get('skip_cost_account_move', False):
            return []
        return super(ProductProduct, self)._anglo_saxon_sale_move_lines(name, product, uom, qty, price_unit, currency, amount_currency, fiscal_position, account_analytic, analytic_tags)
