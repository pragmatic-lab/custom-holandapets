# -*- coding: utf-8 -*-
# Part of SnepTech. See LICENSE file for full copyright and licensing details.##
###############################################################################

from odoo import api, fields, models, _

class product_template(models.Model):
    
    _inherit = 'product.product'
    
    product_variant_pricelist_ids = fields.One2many('product.pricelist.item','product_id','Pricelist Items')



