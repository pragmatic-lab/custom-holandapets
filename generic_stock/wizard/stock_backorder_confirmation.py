from odoo import api, fields, models, _


class StockBackorderConfirmation(models.TransientModel):    
    _inherit = 'stock.backorder.confirmation'

    def process_cancel_backorder(self):
        #pasar contexto para que al seleccionar <no crear backorder>
        #el sistema deja el picking en estado cancelado pero genera secuencias
        #por ello pasar contexto para que no genere secuencias al duplicar el picking
        return super(StockBackorderConfirmation, self.with_context(cancel_backorder=True)).process_cancel_backorder()
