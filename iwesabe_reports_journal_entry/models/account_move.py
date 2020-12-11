# -*- coding: utf-8 -*-

from odoo import models


class AccMoveReport(models.Model):
    _inherit = 'account.move'

    def print_journal_entry(self):
        return self.env.ref('iwesabe_reports_journal_entry.action_report_journal_entry').report_action(self)