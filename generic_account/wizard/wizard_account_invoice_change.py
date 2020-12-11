from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class WizardAccountInvoiceChange(models.TransientModel):
    _name = 'wizard.account.invoice.change'
    _description = 'Asistente para cambiar asientos contables de facturas validadas'
    
    date_invoice = fields.Date(string='Fecha de Emision', copy=False)
    account_id = fields.Many2one('account.account', string='Cuenta Contable')
    journal_id = fields.Many2one('account.journal', string='Diario Contable')
    line_ids = fields.One2many('wizard.account.invoice.change.line', 'wizard_id', string='Líneas')
    company_id = fields.Many2one('res.company', string='Compañía')
    document_type = fields.Selection([
        ('out_invoice','Customer Invoice'),
        ('in_invoice','Supplier Invoice'),
        ('out_refund','Customer Refund'),
        ('in_refund','Supplier Refund'),
        ], string='Tipo')     
    account_type = fields.Selection([
        ('other', 'Regular'),
        ('receivable', 'Receivable'),
        ('payable', 'Payable'),
        ('liquidity', 'Liquidity'),
        ], string='Tipo de Cuenta')

    @api.model
    def write_line_data(self, line):
        params = {
            'account_id': line.account_id.id,
            'account_analytic_id': line.account_analytic_id.id or None,
            'description': line.description,
            'invoice_line_id': line.invoice_line_id.id,
        }
        SQL = """
            UPDATE account_invoice_line 
                SET account_id = %(account_id)s,
                    account_analytic_id = %(account_analytic_id)s,
                    name = %(description)s
            WHERE id = %(invoice_line_id)s
        """
        self._cr.execute(SQL, params)
        line.invoice_line_id.write({'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)]})
        return True
    
    @api.multi
    def update_date_invoice(self, invoice):
        #Actualizacion de Fecha de Factura y recalculo de terminos de pago y fecha de vencimiento
        if self.date_invoice != invoice.date_invoice:
            invoice.write({
                'date_invoice': self.date_invoice,
                'date': False,
            })
            invoice.action_date_assign()
        return True
    
    @api.multi
    def update_account_invoice(self, invoice):
        #Actualizacion de Fecha de Factura y recalculo de terminos de pago y fecha de vencimiento
        if self.account_id != invoice.account_id:
            invoice.write({
                'account_id': self.account_id.id,
            })
        return True
    
    @api.multi
    def _remove_reconcile(self, invoice):
        #al romper conciliacion pasar por context la factura para que se quite de los pagos
        invoice.payment_move_line_ids.with_context(invoice_id=invoice.id).remove_move_reconcile()
        return True
    
    @api.multi
    def _reconcile_payments(self, invoice, payment_recs):
        #volver a asociar los pagos que tenia la factura
        for payment in payment_recs:
            invoice.register_payment(payment)
        return True
        
    @api.multi
    def action_change_move(self):
        self.ensure_one()
        invoice = self.env['account.invoice'].browse(self.env.context.get('active_ids', [])[0])
        payment_recs = invoice.payment_move_line_ids
        self.update_account_invoice(invoice)
        self.update_date_invoice(invoice)
        for line in self.line_ids:
            self.write_line_data(line)
        move = invoice.move_id
        self._remove_reconcile(invoice)
        self.env.cr.execute('''
            UPDATE account_invoice 
                SET move_id = null
            WHERE id = %(invoice_id)s
        ''', {'invoice_id': invoice.id})
        move.button_cancel()
        self.env.cr.execute("DELETE FROM account_move WHERE id = %(id)s", {'id': move.id})
        #Se crea nuevamnete el movimiento contable
        invoice.action_move_create()
        self._reconcile_payments(invoice, payment_recs)
        return {'type': 'ir.actions.act_window_close'}


class WizardAccountInvoiceChangeLine(models.TransientModel):
    _name = 'wizard.account.invoice.change.line'
    _description = 'Detalle de Asistente para cambiar asientos contables'

    wizard_id = fields.Many2one('wizard.account.invoice.change', 
        string='Asistente', ondelete="cascade")
    account_id = fields.Many2one('account.account', string='Cuenta Contable', required=True)
    description = fields.Char(string='Descripción', required=True)
    product_id = fields.Many2one('product.product', readonly=True, string='Producto')
    account_analytic_id = fields.Many2one('account.analytic.account',
        string='Cuenta Analitica')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Etiquetas Analiticas') 
    invoice_line_id = fields.Many2one('account.invoice.line', string='Línea de Factura') 
    taxes_ids = fields.Many2many('account.tax', 'wizard_change_tax_rel', 
        'wizard_id', 'tax_id', readonly=True, string='Impuestos')
    price_unit = fields.Float('Precio Unitario', readonly=True, 
        digits=dp.get_precision('Product Price'))
    quantity = fields.Float('Cantidad', readonly=True,
        digits=dp.get_precision('Product Unit of Measure'))
    discount = fields.Float(string='Descuento(%)', readonly=True,
        digits=dp.get_precision('Discount'))
    price_subtotal = fields.Float('Subtotal', readonly=True, 
        digits=dp.get_precision('Account'))
