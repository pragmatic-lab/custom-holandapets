from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _

class StockMove(models.Model):
    _inherit = 'stock.move'
    
    pos_order_line_id = fields.Many2one('pos.order.line', u'Linea de pedido POS')
    
    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        distinct_fields = super(StockMove, self)._prepare_merge_moves_distinct_fields()
        distinct_fields.append('pos_order_line_id')
        return distinct_fields
    
    @api.model
    def _prepare_merge_move_sort_method(self, move):
        move.ensure_one()
        keys_sorted = super(StockMove, self)._prepare_merge_move_sort_method(move)
        keys_sorted.append(move.pos_order_line_id.id)
        return keys_sorted
    
    @api.multi
    def _action_propagate_valuation(self):
        for move in self.filtered('pos_order_line_id'):
            # las ventas tienen signo negativo, por ello multiplicar x -1
            # las devoluciones al ser entradas tendrian signo positivo y al multiplicar por -1 quedan en negativo
            move.pos_order_line_id.write({'amount_cost': move.value * -1})
        return super(StockMove, self)._action_propagate_valuation()