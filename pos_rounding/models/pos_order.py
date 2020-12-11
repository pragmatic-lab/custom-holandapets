import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

class PosOrder(models.Model):
    _inherit = "pos.order"

    is_rounding = fields.Boolean("Tiene Redondeo?")
    rounding_option = fields.Selection([
        ("digits", 'Digitos'), 
        ('points','Precision'),
    ], string='Opcion de redondeo', default='digits')
    rounding = fields.Float(string='Redondeo', digits=0,readonly=True)

    @api.model
    def _order_fields(self, ui_order):
        order_vals = super(PosOrder, self)._order_fields(ui_order)
        if ui_order.get('rounding'):
            order_vals['rounding'] = ui_order.get('rounding')
        return order_vals
    
    @api.model
    def _process_order(self, pos_order):
        order = super(PosOrder, self)._process_order(pos_order)
        if order.rounding:
            rounding_journal_id = order.session_id.config_id.rounding_journal_id
            if rounding_journal_id:
                order.add_payment({
                    'amount': order.rounding * -1,
                    'payment_name': 'Redondeo',
                    'journal': rounding_journal_id.id,
                })
        return order
    
    def _reconcile_payments(self):
        order_with_rounding = self.filtered(lambda x: x.rounding)
        orders_normal = self - order_with_rounding
        if orders_normal:
            super(PosOrder, orders_normal)._reconcile_payments()
        for order in order_with_rounding:
            aml = order.statement_ids.mapped('journal_entry_ids') | order.account_move.line_ids | order.invoice_id.move_id.line_ids
            aml = aml.filtered(lambda r: not r.reconciled and r.account_id.internal_type == 'receivable' and r.partner_id == order.partner_id.commercial_partner_id)

            # de base se separa los negativos de positivos para no mezclar devoluciones
            # sin embargo cuando hay redondeo no debe hacerse eso, ya que no se concilian bien los valores 
            
            # Reconcile returns first
            # to avoid mixing up the credit of a payment and the credit of a return
            # in the receivable account
            #aml_returns = aml.filtered(lambda l: (l.journal_id.type == 'sale' and l.credit) or (l.journal_id.type != 'sale' and l.debit))
            try:
                #aml_returns.reconcile()
                #(aml - aml_returns).reconcile()
                aml.reconcile()
            except Exception:
                # There might be unexpected situations where the automatic reconciliation won't
                # work. We don't want the user to be blocked because of this, since the automatic
                # reconciliation is introduced for convenience, not for mandatory accounting
                # reasons.
                # It may be interesting to have the Traceback logged anyway
                # for debugging and support purposes
                _logger.exception('Reconciliation did not work for order %s', order.name)
