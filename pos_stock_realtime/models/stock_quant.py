# -*- coding: utf-8 -*-

from odoo import api, fields, models
from collections import deque


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def get_qty_available(self, location_id, location_ids=None, product_ids=None):
        if location_id:
            domain = [
                ('usage', '=', 'internal'),
                ('id', 'child_of', location_id)
            ]
            all_locations = self.env['stock.location'].search(domain)

            stock_quant = self.search_read(
                [('location_id', 'in', all_locations.ids)],
                ['product_id', 'quantity', 'location_id'])
            return stock_quant
        else:
            stock_quant = self.search_read(
                [('location_id', 'in', location_ids),
                 ('product_id', 'in', product_ids)],

                ['product_id', 'quantity', 'location_id'])
            return stock_quant

    @api.model
    def create(self, vals):
        res = super(StockQuant, self).create(vals)
        if res.location_id.usage == 'internal':
            self.env['pos.stock.channel'].broadcast(res)
        return res

    @api.multi
    def write(self, vals):
        record = self.filtered(lambda x: x.location_id.usage == 'internal')
        self.env['pos.stock.channel'].broadcast(record)
        return super(StockQuant, self).write(vals)
