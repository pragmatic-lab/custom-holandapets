from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class PosCategory(models.Model):
    _inherit = 'pos.category'
    
    product_count = fields.Integer(
        '# Products', compute='_compute_product_count',
        help="The number of products under this category (Does not consider the children categories)")

    def _compute_product_count(self):
        read_group_res = self.env['product.template'].read_group([('pos_categ_id', 'in', self.ids)], ['pos_categ_id'], ['pos_categ_id'])
        group_data = dict((data['pos_categ_id'][0], data['pos_categ_id_count']) for data in read_group_res)
        for categ in self:
            categ.product_count = group_data.get(categ.id, 0)
