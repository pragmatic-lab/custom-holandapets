from odoo import models, api, fields
from odoo.exceptions import UserError, ValidationError


class wizard_change_product_category(models.TransientModel):
    _name = 'wizard.change.product.category'
    _description = 'Asistente para cambio de categoria en productos'
    
    product_ids = fields.Many2many('product.product', 
        'wizard_change_product_category_products_rel', 
        'wizard_id', 'product_id', 'Productos')
    product_categ_id = fields.Many2one('product.category', 'Nueva Categoria de Producto')
    acc_move_id = fields.Many2one('account.move', 'Asiento contable Creado')
    
    @api.multi
    def action_change_product_categ(self):
        acc_move_model = self.env['account.move']
        if not self.product_ids:
            raise UserError("Debe seleccionar al menos un producto para poder cambiar de categoria, caso contrario cierre este asistente.")
        product_to_change = self.env['product.product'].browse()
        for product in self.product_ids:
            msj = "<h2 style='color: red;'>ADVERTENCIA</h2>Se cambio de Categoria desde el asistente."
            product.message_post(body=msj)
            product.product_tmpl_id.message_post(body=msj)
            if product.categ_id.property_stock_valuation_account_id != self.product_categ_id.property_stock_valuation_account_id:
                if product.qty_available > 0:
                    product_to_change |= product
        #crear asiento contable de los productos que tienen stock 
        #y la cuenta contable de inventario de la nueva categoria es diferente a la cuenta de inventario de la categoria anterior
        if product_to_change:
            vals_move = self.get_account_vals()
            aml_vals = []
            amount_total = 0.0
            for product in product_to_change:
                move_name = "Cambio de Categoria en Producto: %s" % (product.display_name)
                valuation = product.qty_available * product.standard_price
                amount_total += valuation
                aml_vals.append((0, 0, self.get_account_line_vals(product, vals_move['date'], product.categ_id.property_stock_valuation_account_id.id, move_name, -valuation)))
                aml_vals.append((0, 0, self.get_account_line_vals(product, vals_move['date'], self.product_categ_id.property_stock_valuation_account_id.id, vals_move['ref'], amount_total)))
            vals_move['line_ids'] = aml_vals
            acc_move_rec = acc_move_model.create(vals_move)
            acc_move_rec.post()
            self.acc_move_id = acc_move_rec.id
        self.product_ids.write({'categ_id': self.product_categ_id.id})
        return self.env['odoo.utils'].show_view(name="Proceso Terminado con Exito", model=self._name, id_xml='generic_stock_account.wizard_change_product_category_result_form_view', res_id=self.id)
    
    @api.multi
    def get_account_vals(self):
        date_move = fields.Date.context_today(self)
        move_name = 'Asistente de Cambio de Categoria de Productos'
        vals_acc = {
            'journal_id': self.product_categ_id.property_stock_journal.id,
            'ref': move_name,
            'date': date_move,
        }
        return vals_acc
    
    @api.multi
    def get_account_line_vals(self, product, date_move, account_id, move_name, amount):
        vals_aml = {
            'name': move_name,
            'debit': amount if amount > 0 else 0.0,
            'credit': abs(amount) if amount < 0 else 0.0,
            'account_id': account_id,
            'product_id': product.id,
        }
        return vals_aml
