# -*- coding: utf-8 -*-
from odoo import models

class PosOrder(models.Model):
    _inherit = "pos.order"

    def _payment_fields(self, ui_paymentline):
        res = super(PosOrder, self)._payment_fields(ui_paymentline)
        res.update({
            'payment_ref': ui_paymentline.get('payment_ref'),
        })
        return res

    def add_payment(self, data):
        statement_id = super(PosOrder, self).add_payment(data)
        StatementLine = self.env['account.bank.statement.line']
        statement_lines = StatementLine.search([
            ('statement_id', '=', statement_id),
            ('pos_statement_id', '=', self.id),
            ('journal_id', '=', data['journal']),
            ('amount', '=', data['amount'])
        ])
        for line in statement_lines:
            if line.journal_id.pos_payment_ref :

                card_vals = {
                    'payment_ref': data.get('payment_ref'),
                }
                line.write(card_vals)
                break

        return statement_id
