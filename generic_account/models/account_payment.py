from odoo import models, api, fields, tools


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.multi
    def action_draft(self):
        res = super(AccountPayment, self).action_draft()
        self.write({'move_name': False})
        return res
