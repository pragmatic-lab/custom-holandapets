# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2015 Dynexcel (<http://dynexcel.com/>).
#
##############################################################################
import pytz
import time

from odoo import models, fields, api
from odoo.exceptions import ValidationError, Warning
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime


class CustomReport(models.AbstractModel):
    _name = "report.de_partner_statement.de_partner_ledger_pdf_report"

    def _get_report_values(self,docids,data=None):
        query_get_location = ''
        
        cr = self._cr
        query = """select sum(l.debit - l.credit) as opening_bal
from account_move_line l
join account_move m on l.move_id = m.id
join account_account a on l.account_id = a.id
where a.reconcile = True
        and l.partner_id = %s and l.date < %s
        """ 
        cr.execute(query, [data['partner_id'],data['start_date']])
        openbal = cr.dictfetchall()

        cr = self._cr
        query = """
        select m.ref,m.name as doc_no, m.date, m.narration, j.name as journal, p.name as partner_name, 
l.name as line_desc, a.name as gl_account, m.currency_id, l.debit, l.credit
from account_move_line l
join account_move m on l.move_id = m.id
join res_partner p on l.partner_id = p.id
join account_account a on l.account_id = a.id
join account_journal j on m.journal_id = j.id
where a.reconcile = True
        and l.partner_id = %s and (m.date between %s and %s)
        order by m.date
        """ 
        cr.execute(query, [data['partner_id'],data['start_date'],data['end_date']])
        dat = cr.dictfetchall()

        return {
            'doc_ids': self.ids,
            'doc_model': 'partner.ledger',
            'openbal': openbal,
            'dat': dat,
            'data': data,
        }
