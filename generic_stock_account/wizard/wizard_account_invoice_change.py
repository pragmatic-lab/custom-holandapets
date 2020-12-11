from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class WizardAccountInvoiceChange(models.TransientModel):
    _inherit = 'wizard.account.invoice.change'
    
    @api.multi
    def _remove_reconcile(self, invoice):
        res = super(WizardAccountInvoiceChange, self)._remove_reconcile(invoice)
        # romper conciliacion con las cuentas de inventario tambien
        aml_inventory = invoice.move_id.line_ids.filtered(lambda x: x.account_id.internal_type not in ('receivable', 'payable') and x.account_id.reconcile)
        if aml_inventory:
            aml_inventory.with_context(invoice_id=invoice.id).remove_move_reconcile()
        return res
    
    @api.multi
    def _reconcile_payments(self, invoice, payment_recs):
        res = super(WizardAccountInvoiceChange, self)._reconcile_payments(invoice, payment_recs)
        invoice._anglo_saxon_reconcile_valuation()
        return res
