from odoo import models, api, fields, tools


class PosOrder(models.Model):
    _inherit = 'pos.order'
    
    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(PosOrder, self)._order_fields(ui_order)
        if ui_order.get('note'):
            order_fields['note'] = ui_order['note']
        return order_fields


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'
    
    note = fields.Char('Notas')
