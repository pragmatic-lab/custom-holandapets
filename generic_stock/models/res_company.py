from odoo import models, api, fields


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    stock_policy = fields.Selection([
        ('control_stock','No Permitir movimiento sin inventario'),
        ('no_control_stock','Permitir Movimientos sin Inventario'),
    ], string='Política de Inventarios', readonly=False, default='no_control_stock')
    location_showed_ids = fields.Many2many('stock.location', 'res_company_location_showed_rel', 
        'company_id', 'location_id', string='Ubicaciones Mostradas en V. Lista') 
