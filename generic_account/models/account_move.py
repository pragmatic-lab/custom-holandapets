from odoo import models, api, fields
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'
    
    @api.multi
    def post(self, invoice=False):
        if self.env.user.company_id.restrict_current_period:
            for move in self:
                today = fields.Date.context_today(self)
                if move.date.strftime('%m') != today.strftime('%m'):
                    raise UserError("Usted se encuenta en el mes de: %s, no puede ingresar un movimiento con fecha %s del mes de: %s" % 
                                    (today.strftime('%B').capitalize(), move.date, move.date.strftime('%B').capitalize()))
        return super(AccountMove, self).post(invoice=invoice)
