from collections import OrderedDict

from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class ReportAccountMoveParser(models.AbstractModel):
    _name = 'report.generic_account.report_account_move'
    _description = "Reporte de Asiento contable"
    
    @api.model
    def get_lines(self, move):
        lines_data = OrderedDict()
        line_key = False
        default_data = {
            'name': '',
            'account_display_name': '',
            'debit': 0,
            'credit': 0,
        }
        for line in move.line_ids:
            line_key = line.id
            if self.env.context.get('print_grouped', False):
                line_key = line.account_id
            lines_data.setdefault(line_key, default_data.copy())
            lines_data[line_key].update({
                'name': line.name,
                 'account_display_name': line.account_id.display_name,
            })
            lines_data[line_key]['debit'] += line.debit
            lines_data[line_key]['credit'] += line.credit
        return lines_data.values()
    
    @api.model
    def get_total_debit(self, move):
        debit = 0.0
        for line in move.line_ids:
            debit += line.debit
        return debit
    
    @api.model
    def get_total_credit(self, move):
        credit = 0.0
        for line in move.line_ids:
            credit += line.credit
        return credit
    
    @api.model
    def _get_report_values(self, docids, data=None):
        if not data:
            data = {}
        move_model = self.env['account.move']
        docargs = {
            'doc_ids': docids,
            'doc_model': move_model._name,
            'data': data,
            'docs': move_model.browse(docids),
            'get_lines': self.get_lines,
            'get_total_debit': self.get_total_debit,
            'get_total_credit': self.get_total_credit,
        }
        return docargs


class ReportAccountMoveGroupedParser(models.AbstractModel):
    _name = 'report.generic_account.report_account_move_grouped'
    _description = "Reporte de Asiento contable Agrupado"
        
    @api.model
    def _get_report_values(self, docids, data=None):
        if not data:
            data = {}
        docargs = self.env['report.generic_account.report_account_move'].with_context(print_grouped=True)._get_report_values(docids, data)
        docargs['print_grouped'] = True
        return docargs
