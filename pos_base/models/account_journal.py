from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _

class AccountJournal(models.Model):

    _inherit = 'account.journal'
    
    # este campo debe extenderse en modulo de redondeo, NC, loyalty, etc
    use_in_pos_for = fields.Selection([('none', 'Ninguno')], string="Usar Diario para",)
    