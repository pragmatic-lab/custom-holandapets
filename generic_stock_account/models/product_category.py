from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class ProductCategory(models.Model):
    _inherit = ['mail.thread', 'product.category']
    _name = 'product.category'
    
    #reemplazar campos para agregar track_visibility
    property_stock_account_input_categ_id = fields.Many2one('account.account', 
        track_visibility='onchange', company_dependent=True)
    property_stock_account_output_categ_id = fields.Many2one('account.account', 
        track_visibility='onchange', company_dependent=True)
    property_stock_valuation_account_id = fields.Many2one('account.account', 
        track_visibility='onchange', company_dependent=True)
    property_account_income_categ_id = fields.Many2one('account.account', 
        track_visibility='onchange', company_dependent=True)
    property_account_expense_categ_id = fields.Many2one('account.account', 
        track_visibility='onchange', company_dependent=True)
    
    @api.onchange('property_stock_valuation_account_id',)
    def _onchange_property_stock_valuation_account(self):
        warning = {}
        if self.property_stock_valuation_account_id and self._origin:
            if self.property_stock_valuation_account_id != self._origin.property_stock_valuation_account_id and self.product_count > 0:
                warning = {'title': 'ADVERTENCIA',
                           'message': 'Uno o mas productos ligados a esta categoria podrian afectarse con este cambio de cuenta contable'
                           }
        res = {'warning': warning}
        return res 

    @api.multi
    def write(self, vals):
        categ_changed = self.browse()
        if 'property_stock_valuation_account_id' in vals:
            categ_changed = self.filtered(lambda x: x.property_stock_valuation_account_id.id != vals['property_stock_valuation_account_id'])
        res = super(ProductCategory, self).write(vals)
        #cuando cambie la cuenta de valoracion de inventario
        #verificar si hay productos en esa categoria, dejar un mensaje de advertencia
        if 'property_stock_valuation_account_id' in vals:
            for categ in categ_changed:
                if categ.product_count > 0:
                    msj = []
                    msj.append("<h2 style='color: red;'>ADVERTENCIA</h2><br/>")
                    msj.append("Uno o mas productos ligados a esta categoria podrian afectarse con este cambio de cuenta contable")
                    msj = "".join(msj)
                    categ.message_post(body=msj)
        return res
