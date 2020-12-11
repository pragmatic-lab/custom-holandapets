from odoo import models, fields, api, _

class AccountJournal(models.Model):
    _inherit = "account.journal"
    
    # Agregar opcion de Redondeo para que estos diarios no se muestren en el POS como forma de pago
    use_in_pos_for = fields.Selection(selection_add=[('rounding', 'Redondeo')])