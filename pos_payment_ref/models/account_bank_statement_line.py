# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    pos_payment_ref = fields.Boolean(related='journal_id.pos_payment_ref', readonly=True)
    payment_ref = fields.Char('Bank Name')