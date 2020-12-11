from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class InvoiceDueList(models.TransientModel):
    _name = 'account.invoice.due.list'
    _description = 'List Due Invoices'

    date = fields.Date(string='Due Date', required=True, default=fields.Date.context_today)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get('account.invoice'))

    @api.multi
    def list_due_invoices(self):
        invoice_type = self._context.get('invoice_type', 'out_invoice')
        invoice_args = [('company_id', '=', self.company_id.id), ('state', '=', 'open'),
                        ('type', '=', invoice_type), ('date_due', '<=', self.date)]
        invoices = self.env['account.invoice'].search(invoice_args)

        if invoice_type in ('out_invoice', 'in_refund'):
            action = self.env['ir.actions.act_window'].for_xml_id('account', 'action_invoice_tree1')
            action['display_name'] = _('Customer invoices due on or before %s' % (self.date))
        else:
            action = self.env['ir.actions.act_window'].for_xml_id('account', 'action_vendor_bill_template')
            action['display_name'] = _('Vendor invoices due on or before %s' % (self.date))
        action['domain'] = [('id', 'in', invoices.ids)]
        print(action)
        return action
