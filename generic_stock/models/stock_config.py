from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class StockConfig(models.TransientModel):
    _inherit = 'res.config.settings'
    
    stock_policy = fields.Selection([
        ('control_stock','No Permitir movimiento sin inventario'),
        ('no_control_stock','Permitir Movimientos sin Inventario'),
        ], string='Control de Stock en Negativo', default='no_control_stock', 
        related='company_id.stock_policy', readonly=False,)
    location_showed_ids = fields.Many2many('stock.location', 'stock_config_settings_location_rel', 
        'config_id', 'location_id', string='Ubicaciones Mostradas en V. Lista', 
        related='company_id.location_showed_ids', readonly=False,)
    group_set_date_movement_picking = fields.Boolean("Especificar Fechas de inventario",
        help='Los albaranes por lo general al procesarse toman la fecha actual, '\
            'al permitir especificar fechas se puede procesar inventario con fecha pasada',
        implied_group='generic_stock.group_set_date_movement_picking')
