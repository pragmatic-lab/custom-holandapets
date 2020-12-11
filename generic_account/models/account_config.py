from odoo import models, api, fields


class AccountConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    restrict_current_period = fields.Boolean('Verificar Fecha de Asiento en Mismo Periodo?', 
        related='company_id.restrict_current_period', readonly=False,
        help="Marque esta opcion si no se permite asentar asientos contables fuera del mes actual",)
