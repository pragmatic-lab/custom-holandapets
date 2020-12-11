from odoo import models, api, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    restrict_current_period = fields.Boolean('Verificar Fecha de Asiento en Mismo Periodo?', readonly=False, 
        help="Marque esta opcion si no se permite asentar asientos contables fuera del mes actual",)
