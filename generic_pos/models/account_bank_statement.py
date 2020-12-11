from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.tools import formatLang


class AccountBankStatement(models.Model):    
    _inherit = 'account.bank.statement'

    @api.multi
    def name_get(self):
        res = []
        if self.env.context.get('name_pos', False):
            for element in self:
                name = "%s" % (element.journal_id.display_name)
                res.append((element.id, name))
        elif self.env.context.get('name_include_pos', False):
            for element in self:
                name = "%s" % (element.journal_id.display_name)
                if element.pos_session_id:
                    name += " - %s" % element.pos_session_id.config_id.display_name
                res.append((element.id, name))
        else:
            res = super(AccountBankStatement, self).name_get()
        return res


class AccountBankStatementLine(models.Model):    
    _inherit = 'account.bank.statement.line'
    
    @api.multi
    def name_get(self):
        res = []
        if self.env.context.get('name_pos', False):
            for element in self:
                name = "%s(Monto: %s)" % (element.journal_id.display_name, formatLang(self.env, element.amount, monetary=True))
                res.append((element.id, name))
        else:
            res = super(AccountBankStatementLine, self).name_get()
        return res
