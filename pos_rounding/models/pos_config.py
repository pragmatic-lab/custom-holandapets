
from odoo import models, fields, api, _

class PosConfig(models.Model):
    _inherit = 'pos.config'

    enable_rounding = fields.Boolean("Permitir Redondeo?")
    rounding_option = fields.Selection([
        ("digits", 'Digitos'), 
        ('points','Precision'),
    ], string='Opcion de redondeo', default='digits')
    rounding_journal_id = fields.Many2one('account.journal',"Diario de redondeo")
    rounding_precision = fields.Float("Precision de redondeo", default=lambda *a: 2)

    @api.onchange('journal_ids')
    def _onchange_journal_ids(self):
        if self.rounding_journal_id not in self.journal_ids:
            self.rounding_journal_id = False
