from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class PosConfig(models.Model):
    _inherit = 'pos.config'
    
    enable_order_note = fields.Boolean('Notas en Pedidos?')
    print_order_note = fields.Boolean('Imprimir las Notas en Ticket?')
    enable_order_line_note = fields.Boolean('Notas en Lineas del Pedido?')
    print_order_line_note = fields.Boolean('Imprimir las Notas en Ticket?')
    
    @api.onchange('enable_order_note',)
    def _onchange_enable_order_note(self):
        if not self.enable_order_note:
            self.print_order_note = False
            
    @api.onchange('enable_order_line_note',)
    def _onchange_enable_order_line_note(self):
        if not self.enable_order_line_note:
            self.print_order_line_note = False
