from lxml import etree
from collections import defaultdict

from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, ValidationError


class ProductProduct(models.Model):    
    _inherit = 'product.product'
    
    @api.depends()
    def _get_stock_by_location(self):
        company = self.env.user.company_id
        ctx_loc = self.env.context.copy()
        if company.location_showed_ids and self.env.user.has_group('generic_stock.group_see_stock_by_location'):
            for location in company.location_showed_ids:
                ctx_loc['location'] = location.id
                ctx_loc['show_all_stock'] = True #pasar esto para que en intersport no se filtre la bodega del usuario que tiene pocos permisos
                quantities_dict =  self.with_context(ctx_loc)._compute_quantities_dict(ctx_loc.get('lot_id'), ctx_loc.get('owner_id'), ctx_loc.get('package_id'), ctx_loc.get('from_date'), ctx_loc.get('to_date'))
                for product in self:
                    product['stock_loc_%s' % location.id] = quantities_dict[product.id]['qty_available']
    
    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super(ProductProduct, self).fields_get(allfields, attributes)
        company = self.env.user.company_id
        if company.location_showed_ids and self.env.user.has_group('generic_stock.group_see_stock_by_location'):
            cls = type(self)
            groups = defaultdict(list)
            for location in company.location_showed_ids:
                new_field = fields.Float(location.display_name, 
                                         digits=dp.get_precision('Product Unit of Measure'), 
                                         readonly=True, store=False, compute='_get_stock_by_location')
                name = 'stock_loc_%s' % location.id
                self._add_field(name, new_field)
                cls._field_computed[new_field] = groups[new_field.compute]
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        company = self.env.user.company_id
        util_model = self.env['odoo.utils']
        precision_digits = dp.get_precision('Product Unit of Measure')(self.env.cr)
        precision_digits = precision_digits and precision_digits[1] or 2
        res = super(ProductProduct, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'tree' and company.location_showed_ids and self.env.user.has_group('generic_stock.group_see_stock_by_location'):
            doc = etree.XML(res['arch'])
            nodes = util_model.find_node(doc, 'qty_available')
            if nodes:
                node = nodes [0]
                parent_map = dict((c, p) for p in doc.getiterator() for c in p)
                parent = parent_map.get(node, False)
                node_index = parent.getchildren().index(node) + 1
                if len(parent):
                    for location in company.location_showed_ids:
                        name_field = 'stock_loc_%s' % location.id
                        new_node = etree.Element('field', {'name': name_field,
                                                           'readonly': '1'})
                        parent.insert(node_index, new_node)
                        node_index += 1
                        if name_field not in res['fields']:
                            location_name = location.name
                            if location.location_id:
                                location_name = location.location_id.name + ' / ' + location.name  
                            res['fields'][name_field] = {
                                             'type': 'float',
                                             'digits': (16, precision_digits),
                                             'searchable': True,
                                             'readonly': 1,
                                             'store': False,
                                             'string': location_name,
                                             }
            res['arch'] = etree.tostring(doc)
        return res
    
    @api.multi
    def _set_standard_price(self, value):
        ''' Store the standard price change in order to be able to retrieve the cost of a product for a given date'''
        PriceHistory = self.env['product.price.history']
        for product in self:
            history_vals = {
                'product_id': product.id,
                'cost': value,
                'company_id': self._context.get('force_company', self.env.user.company_id.id),
            }
            if self.env.context.get('save_cost_reason'):
                history_vals['reason'] = self.env.context.get('save_cost_reason')
            if self.env.context.get('date_for_move'):
                history_vals['datetime'] = self.env.context.get('date_for_move')
            PriceHistory.create(history_vals)
    
    @api.multi
    def action_view_cost_history(self):
        action = self.env.ref('generic_stock.product_price_history_action').read()[0]
        action['domain'] = [('product_id', 'in', self.ids)]
        return action
