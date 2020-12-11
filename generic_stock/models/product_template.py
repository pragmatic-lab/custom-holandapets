from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    categ_id = fields.Many2one('product.category',
        track_visibility='onchange')
    
    @api.multi
    def action_view_cost_history(self):
        return self.mapped('product_variant_ids').action_view_cost_history()
    
    @api.model
    def get_groups_see_cost_product(self):
        return super(ProductTemplate, self).get_groups_see_cost_product() + ['stock.group_stock_manager']
