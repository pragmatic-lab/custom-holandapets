from lxml import etree

from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ProductProduct, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            util_model = self.env['odoo.utils']
            user_model = self.env['res.users']
            if not any(map(user_model.has_group, self.env['product.template'].get_groups_see_cost_product())):
                doc = etree.XML(res['arch'])
                util_model.find_set_node(doc, 'update_cost_price', {'invisible': True}, 'div')
                util_model.find_set_node(doc, 'action_view_cost_history', {'invisible': True}, 'button')
                res['arch'] = etree.tostring(doc)
        return res
