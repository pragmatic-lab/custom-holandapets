from odoo import models, api, fields
from odoo.exceptions import UserError, ValidationError


class WizardChangeTaxProducts(models.TransientModel):
    _name = 'wizard.change.tax.products'
    _description = 'Asistente para cambio de impuesto en productos'
    
    sale_tax_ids = fields.Many2many('account.tax', 'wizard_sale_tax_rel', 
        'wizard_id', 'tax_id', 'Impuestos de Ventas')
    purchase_tax_ids = fields.Many2many('account.tax', 'wizard_purchase_tax_rel', 
        'wizard_id', 'tax_id', 'Impuestos de Compras')
    change_tax_all_products = fields.Boolean('Cambiar Impuestos a todos los productos?', 
        readonly=False, help="Marque la opcion si desea cambiar los impuestos a productos existentes," \
            "caso contrario los nuevos impuestos seran para nuevos productos", )
        
    @api.multi
    def action_set_default_tax(self):
        # hacerlo como admin para saltar la regla de registro 
        # que permite eliminar solo registros creados por el mismo usuario
        IrDefault = self.env['ir.default'].sudo()
        default_tax = []
        if not self.sale_tax_ids or not self.purchase_tax_ids:
            raise UserError("Debe seleccionar al menos un impuesto para ventas y un impuesto para compras, por favor verifique")
        self.env.user.company_id.write({
            'account_sale_tax_id': self.sale_tax_ids.ids[0],
            'account_purchase_tax_id': self.purchase_tax_ids.ids[0],
        })
        default_tax.append(('taxes_id', self.sale_tax_ids.ids))
        default_tax.append(('supplier_taxes_id', self.purchase_tax_ids.ids))
        for field_name, value in default_tax:
            IrDefault.set('product.template', field_name, value, company_id=self.env.user.company_id.id)
        if self.change_tax_all_products:
            #TODO: para muchos productos hacer el cambio por SQL
            all_products = self.env['product.template'].search([])
            all_products.write({
                'taxes_id': [(6, 0, self.sale_tax_ids.ids)],
                'supplier_taxes_id': [(6, 0, self.purchase_tax_ids.ids)],
            })
        return {'type':'ir.actions.act_window_close' }
