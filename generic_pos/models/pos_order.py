from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp

class PosOrder(models.Model):
    _inherit = ['mail.thread', 'pos.order']
    _name = 'pos.order'
    
    @api.multi
    def _get_key_tax_grouped(self, line):
        # no agrupar por producto, pero en otro modulo quizas sea necesario
        # en Ecuador por ejemplo se deberia agrupar para los productos ICE
        product = False
        tax_key = (False, False, product, line.tax_ids)
        return tax_key
    
    @api.multi
    def get_tax_grouped(self):
        """
        Acumular el subtotal antes de calcular el impuesto
        esto para evitar problemas al calcular el impuesto por linea, al redondear se obtienen datos errados
        acumulando el valor se obtiene mayor precision.
        la acumulacion de valores sera por la cuenta contable, cuenta analitica e impuestos
        solo cuando sea un producto con ICE, agregar el producto para el calculo correcto.
        Para descuentos, no calcular el % de descuento y luego el subtotal restando el % de descuento
        eso trae problemas de descuento, hay que calcular el valor del descuento y eso restarlo al subtotal, ejemplo:
        Cantidad 3, Precio Unit 0,9 Descuento 15%
        ***Erroneo*** 
        Subtotal = 2,7 
        Descuento 0,405(si redondeamos seria 0,41)
        subtotal con descuento 2,7 * 0.85 = 2,295(si redondeamos 2.3)
        ***Correcto***
        Subtotal = 2,7 
        Descuento 0,405(si redondeamos seria 0,41)
        subtotal con descuento 2,7 - 0,41 = 2,29
        *********************************************************
        Con el primer calculo tendriamos una diferencia de 1
        pero el valor correcto seria 2,9 esto se soluciona en el segundo ejemplo
        """
        self.ensure_one()
        default_data = {'subtotal': 0.0, 'discount_total': 0.0, 'quantity_sum': 0.0}
        tax_data = {}
        tax_key = False
        for line in self.lines:
            tax_key = self._get_key_tax_grouped(line)
            tax_data.setdefault(tax_key, default_data.copy())
            tax_data[tax_key]['discount_total'] += line._get_discount_total()
            tax_data[tax_key]['subtotal'] += (line.price_unit * line.qty)
            tax_data[tax_key]['quantity_sum'] += line.qty
        return tax_data

    currency_id = fields.Many2one('res.currency', 'Moneda', 
        default=lambda self: self.env.user.company_id.currency_id)
    tax_ids = fields.One2many('pos.order.tax', 'order_id', 'Impuestos', readonly=True)
    config_id = fields.Many2one('pos.config', 'TPV', related='session_id.config_id', store=True, index=True, auto_join=True)
    commercial_partner_id = fields.Many2one('res.partner', string='Commercial Entity', compute_sudo=True,
        related='partner_id.commercial_partner_id', store=True, readonly=True,
        help="The commercial entity that will be used on Journal Entries for this invoice")
    commercial_parent_id = fields.Many2one('res.partner', string='Contacto Principal', compute_sudo=True,
        related='partner_id.parent_id', store=True, readonly=True)
    payment_term_id = fields.Many2one('account.payment.term', 'Forma de Pago', 
        index=True, copy=False, readonly=True, states={'draft':[('readonly',False)]})
    
    @api.multi
    def _prepare_tax_line_vals(self, tax):
        """ Prepare values to create an pos.order.tax line
        """
        vals = {
            'order_id': self.id,
            'tax_id': tax['id'],
            'amount': tax['amount'],
            'base': tax['base'],
        }
        return vals
    
    @api.multi
    def get_taxes_values(self):
        tax_grouped = {}
        tax_data = self.get_tax_grouped()
        for (account, account_analytic, product, tax_recs), total_data in tax_data.items():
            discount_total = tools.float_round(total_data['discount_total'], precision_digits=self.currency_id.decimal_places)
            subtotal = tools.float_round(total_data['subtotal'], precision_digits=self.currency_id.decimal_places)
            values = tax_recs.compute_all(subtotal - discount_total, quantity=1, product=product, partner=self.partner_id)
            for tax in values['taxes']:
                val = self._prepare_tax_line_vals(tax)
                key = tax['id'] #agrupar por impuesto
                if key not in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
        for val in list(tax_grouped.values()):
            val['amount'] = tools.float_round(val['amount'], precision_digits=self.currency_id.decimal_places)
            val['base'] = tools.float_round(val['base'], precision_digits=self.currency_id.decimal_places)
        return tax_grouped
    
    @api.multi
    def compute_taxes(self):
        """Function used in other module to compute the taxes on a fresh invoice created (onchanges did not applied)"""
        pos_order_tax = self.env['pos.order.tax']
        for order in self:
            # Delete non-manual tax lines
            self._cr.execute("DELETE FROM pos_order_tax WHERE order_id=%s ", (order.id,))
            self.invalidate_cache()
            # Generate one tax line per tax, however many invoice lines it's applied to
            tax_grouped = order.get_taxes_values()
            # Create new tax lines
            for tax in list(tax_grouped.values()):
                pos_order_tax.create(tax)
        return True
    
    @api.multi
    def action_pos_order_paid(self):
        orders = self.filtered(lambda x: not x.tax_ids)
        if orders:
            orders.compute_taxes()
        result = super(PosOrder, self).action_pos_order_paid()
        return result
    
    def _get_valid_session(self, order):
        #cuando desde el pos hay ordenes pendientes de sincronizar, pero la sesion ya fue cerrada
        #el sistema tratara de crear una nueva sesion
        #antes de hacer eso, primero verificar si existe una sesion ya abierta previamente
        current_sesion = self._default_session()
        if not current_sesion:
            current_sesion = super(PosOrder, self)._get_valid_session(order)
        return current_sesion

    def _prepare_stock_move_vals(self, line, order_picking, return_picking, picking_type, return_pick_type, location_id, destination_id):
        move_vals = super(PosOrder, self)._prepare_stock_move_vals(line, order_picking, return_picking, picking_type, return_pick_type, location_id, destination_id)
        if line._name == 'pos.order.line': # puede ser de otro modelo tambien que se llame a esta funcion
            move_vals['pos_order_line_id'] = line.id
        return move_vals
    
    def _prepare_invoice_line(self, line=False, invoice_id=False):
        vals = super(PosOrder, self)._prepare_invoice_line(line, invoice_id)
        vals.update({
            'discount_value': line.discount_value,
            'amount_cost': line.amount_cost,
            'move_line_ids': [(6, 0, line.stock_move_ids.ids)],
        })
        return vals
    
    def _prepare_invoice(self):
        vals = super(PosOrder, self)._prepare_invoice()
        vals.update({
            'picking_ids': [(6, 0, self.picking_id.ids)],
        })
        return vals


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'
    
    discount_value = fields.Float(u'Descuento Monto', digits=dp.get_precision('Account'))
    amount_cost = fields.Float(u'Total Costo', digits=dp.get_precision('Product Price'))
    stock_move_ids = fields.One2many('stock.move', 'pos_order_line_id', u'Movimientos de stock')
    
    @api.multi
    def _get_discount_total(self):
        return (self.discount_value * self.qty) or (self.price_unit * self.qty * self.discount * 0.01)
    
    @api.multi
    def _get_discount_unit(self):
        return (self.price_unit * self.discount * 0.01)


class PosOrderTax(models.Model):
    
    _inherit = "common.document.tax"
    _name = 'pos.order.tax'

    order_id = fields.Many2one('pos.order', string='Orden', ondelete='cascade', index=True)
