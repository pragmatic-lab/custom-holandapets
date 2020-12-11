# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    pos_payment_ref = fields.Boolean('POS Payment Ref', default=False)
