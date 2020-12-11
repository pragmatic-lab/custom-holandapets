from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _ 
from odoo.exceptions import UserError, ValidationError


class AccountInvoice(models.Model):
    _inherit = "account.invoice"
    
    @api.multi
    def _can_split_document(self):
        return self.type in ('out_invoice', 'out_refund')
    
    @api.multi
    def _get_number_lines(self):
        number_lines = 1000 # este numero se deberia personalizar segun cada pais, o empresa
        return number_lines
    
    @api.multi
    def _get_count_invoice_lines(self):
        return len(self.invoice_line_ids)
    
    @api.multi
    def _compute_total_documents(self):
        #si se ha configurado algo en la tienda verificar si se excede en lineas segun dicha configuracion
        document_number = 1
        number_lines = self._get_number_lines()
        invoice_number_lines = self._get_count_invoice_lines()
        if number_lines > 0 and invoice_number_lines > number_lines:
            document_number = self.env['odoo.utils'].compute_total_documents(invoice_number_lines, number_lines)
        return document_number, number_lines
    
    @api.model
    def _get_fields_to_split(self):
        return [
            'name', 'origin', 'date_invoice', 'date_due', 
            'user_id', 'company_id', 'partner_id',
            'type', 'reference', 'comment', 
            'fiscal_position_id', 'payment_term_id', 'account_id', 'currency_id', 
            'journal_id',
            'refund_invoice_id'
        ]
        
    @api.multi
    def _prepare_invoice_to_split(self):
        new_invoice_data = self.read(self._get_fields_to_split())[0]
        new_invoice_data.update({
            'state': 'draft',
            'invoice_line_ids': [],
            'tax_line_ids': [],
        })
        # take the id part of the tuple returned for many2one fields
        for field in new_invoice_data:
            if isinstance(new_invoice_data[field], tuple):
                new_invoice_data[field] = new_invoice_data[field] and new_invoice_data[field][0]
        return new_invoice_data
    
    @api.model
    def split_invoice_document(self, invoice_id):
        '''
        Split the new_invoice_data when the lines exceed the maximum set for the shop
        '''
        invoice_lines = self.env['account.invoice.line'].browse()
        invoice = self.browse(invoice_id)
        #solo para facturas de cliente y NC
        if not invoice._can_split_document():
            return False
        new_invoice = False
        confirm_invoice = self.env.context.get('confirm_invoice', False)
        if invoice.type in ('out_invoice', 'out_refund'):
            number_lines = invoice._get_number_lines()
            document_number, document_lines = invoice._compute_total_documents()
            if document_number > 1:
                new_invoice = self.create(invoice._prepare_invoice_to_split())
                invoice_lines = invoice.invoice_line_ids[number_lines:]
                invoice_lines.write({'invoice_id': new_invoice.id})
                invoice.compute_taxes()
            if new_invoice:
                new_invoice.compute_taxes()
                if confirm_invoice:
                    new_invoice.action_invoice_open()
        return new_invoice and new_invoice.id or False
    
    @api.multi
    def action_check_number_lines(self):
        """
        Funcion para confirmar las facturas
        para facturas de clientes verifica si las lineas son mayores a las permitidas en la configuracion de la tienda
        de ser asi, levanta un asistente para informarle al usuario que se va a partir el documento
        """
        ctx = self.env.context.copy()
        ctx['active_model'] = self._name
        ctx['active_ids'] = self.ids
        wizard_model = self.env['wizard.split.document.manual'].with_context(ctx)
        res = True
        show_wizard = False
        #hacer la validacion unicamente cuando se este confirmando el documento manualmente desde la UI
        for invoice in self:
            #solo para facturas de cliente y NC
            if not invoice._can_split_document():
                continue
            #calcular si es necesario partir el documento xq tiene muchas lineas
            document_number, document_lines = invoice._compute_total_documents()
            if document_number > 1:
                show_wizard = True
                wizard_rec = wizard_model.create({
                    'document_number': document_number,
                    'document_lines': document_lines,
                    'model_name': self._name,
                })
                res = wizard_rec.show_view()
        #llamar a la funcion normal de validacion de facturas
        if not show_wizard:
            res = self.action_invoice_open()
        return res
    
    @api.multi
    def action_cancel(self):
        self.mapped('invoice_line_ids').write({'amount_cost': 0})
        return super(AccountInvoice, self).action_cancel()
    
    @api.multi
    def action_invoice_draft(self):
        res = super(AccountInvoice, self).action_invoice_draft()
        #al reprocesar la factura borrar el nombre del asiento contable
        #para poder eliminar de ser necesario
        self.write({'move_name': ''})
        return res

    @api.multi
    def action_change_account_move(self):
        wizard_model = self.env['wizard.account.invoice.change']
        values = {
            'date_invoice': self.date_invoice,
            'document_type': self.type,
            'company_id': self.company_id.id or self.env.user.company_id.id,
            'journal_id': self.journal_id.id,
            'account_id': self.account_id.id,
            'account_type': self.account_id.internal_type,
            }
        wizard = wizard_model.create(values)
        for line in self.invoice_line_ids.filtered('account_id'):
            wizard.line_ids |= wizard.line_ids.new({
                'invoice_line_id': line.id,
                'product_id': line.product_id.id,
                'account_id': line.account_id.id,
                'description': line.name,
                'account_analytic_id': line.account_analytic_id.id,
                'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)], 
                'taxes_ids': [(6, 0, line.invoice_line_tax_ids.ids)],
                'price_unit': line.price_unit,
                'quantity': line.quantity,
                'discount': line.discount,
                'price_subtotal': line.price_subtotal,
                })
        res = self.env['odoo.utils'].show_action('generic_account.action_wizard_account_invoice_change_view')
        res['res_id'] = wizard.id
        return res


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"
    
    discount_value = fields.Float(u'Descuento(Monto)', digits=dp.get_precision('Account'))
    force_discount_value = fields.Float(u'Descuento total(Monto)', digits=dp.get_precision('Account'))
    amount_cost = fields.Float(u'Total Costo', digits=dp.get_precision('Product Price'), readonly=True)
    price_unit_final = fields.Float('Precio Unitario Final', 
        digits=dp.get_precision('Product Price'), 
        compute='_compute_price_unit_final', store=True)
    
    _sql_constraints = [
        ('discount_limit', 'CHECK (discount <= 100.0)', 'El Descuento debe estar entre 0 y 100, por favor verifique.'),
    ]
    
    @api.depends('price_unit','product_id','discount', 'discount_value')
    def _compute_price_unit_final(self):
        for line in self:
            line.price_unit_final = line._get_price_unit_final()
            
    @api.onchange('discount')
    def _onchange_discount(self):
        self.discount_value = 0
    
    @api.multi
    def _get_discount_total(self):
        discount_total = self.price_unit * self.quantity * self.discount * 0.01
        if self.force_discount_value:
            discount_total = self.force_discount_value
        elif self.discount_value:
            discount_total = self.discount_value * self.quantity
        return discount_total
    
    @api.multi
    def _get_discount_unit(self):
        discount_unit = self.price_unit * self.discount * 0.01
        if self.force_discount_value and self.quantity:
            discount_unit = self.force_discount_value / self.quantity
        elif self.discount_value:
            discount_unit = self.discount_value
        return discount_unit
    
    @api.multi
    def _get_price_unit_final(self):
        # funcion generica para pasar el precio unitario restando el descuento
        currency = self.invoice_id.currency_id
        discount_unit = tools.float_round(self._get_discount_unit(), precision_digits=currency.decimal_places)
        price_unit_final = self.price_unit - discount_unit
        return price_unit_final
