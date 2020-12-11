from odoo import models, api, fields


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    
    @api.model
    def default_get(self, fields):
        values = super(StockReturnPicking, self).default_get(fields)
        product_return_moves = []
        for line in values.get('product_return_moves', []):
            new_line = line[2].copy()
            new_line['to_refund'] = True
            product_return_moves.append((0, 0, new_line))
        values['product_return_moves'] = product_return_moves
        return values
