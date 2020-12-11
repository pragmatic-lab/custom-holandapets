from odoo import models, api, fields


class WizardSplitDocumentManual(models.TransientModel):
    _inherit = 'wizard.split.document.manual'
    
    @api.model
    def _confirm_invoice_automatic(self, invoice):
        confirm_invoice = False
        if not self._is_credit_note(invoice):
            confirm_invoice = True
        return confirm_invoice
        
    @api.model
    def _is_credit_note(self, invoice):
        return invoice.type == 'out_refund'

    @api.model
    def _split_invoice_document(self, invoice):
        invoice_ids = []
        confirm_invoice = self._confirm_invoice_automatic(invoice)
        #no enviar a confirmar la NC, esto se debe hacer al final
        #ya que si se hace al inicio, causa problemas al validar las cantidades de la factura con la NC
        invoice_model2 = self.env['account.invoice'].with_context(confirm_invoice=confirm_invoice)
        invoice_split_id = invoice.id
        while invoice_split_id:
            invoice_split_id = invoice_model2.split_invoice_document(invoice_split_id)
            if invoice_split_id:
                invoice_ids.append(invoice_split_id)
        return invoice_ids
    
    @api.multi
    def _action_split_document(self, active_model, active_ids):
        util_model = self.env['odoo.utils']
        invoice_model = self.env['account.invoice']
        if active_model != invoice_model._name:
            return super(WizardSplitDocumentManual, self)._action_split_document(active_model, active_ids)
        #**********************************
        #PROCESO PARA DIVIDIR FACTURAS
        #**********************************
        invoice_ids = active_ids[:]
        invoice = invoice_model.browse(active_ids[0])
        is_credit_note = self._is_credit_note(invoice)
        invoice_ids.extend(self._split_invoice_document(invoice))
        invoice.action_invoice_open()
        xml_id = 'action_invoice_tree1'
        if is_credit_note:
            #enviar a confirmar las demas NC,las demas facturas se confirman automaticamente, no es necesario
            #se debe hacer en ese orden para que la validacion de montos entre la NC y la factura sea correcto
            invoice_model.browse(invoice_ids).action_invoice_open()
            xml_id = 'action_invoice_out_refund'
        ctx = self.env.context.copy()
        ctx['active_model'] = active_model
        ctx['active_ids'] = invoice_ids
        ctx['active_id'] = invoice_ids and invoice_ids[0] or False
        id_xml = "account.%s" % (xml_id)
        result = util_model.with_context(ctx).show_action(id_xml, [('id', 'in', invoice_ids)])
        return result
