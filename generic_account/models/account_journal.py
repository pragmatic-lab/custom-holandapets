from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class AccountJournal(models.Model):
    _inherit = 'account.journal'
    
    @api.model
    def default_get(self, fields_list):
        values = super(AccountJournal, self).default_get(fields_list)
        values['bank_statements_source'] = 'undefined'
        return values

    @api.multi
    def open_action(self):
        # pasar contexto para que se aplique el filtro de fecha por defecto
        if not self.env.context.get('search_default_draft') and not self.env.context.get('search_default_unpaid'):
            return super(AccountJournal, self.with_context(search_default_this_month=True)).open_action()
        return super(AccountJournal, self).open_action()
