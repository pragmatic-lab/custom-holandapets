from lxml import etree

from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    @api.model
    def get_groups_see_cost_product(self):
        return []
    
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ProductTemplate, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            util_model = self.env['odoo.utils']
            user_model = self.env['res.users']
            if not any(map(user_model.has_group, self.get_groups_see_cost_product())):
                doc = etree.XML(res['arch'])
                util_model.find_set_node(doc, 'update_cost_price', {'invisible': True}, 'div')
                util_model.find_set_node(doc, 'action_view_cost_history', {'invisible': True}, 'button')
                res['arch'] = etree.tostring(doc)
        return res
    
    @api.model_create_multi
    def create(self, vals_list):
        new_recs = super(ProductTemplate, self).create(vals_list)
        # buscar las demas company existentes aparte de la company del producto
        # para asignarle los impuestos al producto en cada company
        for product in new_recs:
            domain = []
            if product.company_id:
                domain.append(('id', '!=', product.company_id.id))
            other_companies = self.env['res.company'].sudo().search(domain)
            for company in other_companies:
                vals_write = {}
                if company.account_sale_tax_id:
                    vals_write['taxes_id'] = [(4, company.account_sale_tax_id.id)]
                if company.account_purchase_tax_id:
                    vals_write['supplier_taxes_id'] = [(4, company.account_purchase_tax_id.id)]
                if vals_write:
                    product.with_context(force_company=company.id).write(vals_write)
        return new_recs
