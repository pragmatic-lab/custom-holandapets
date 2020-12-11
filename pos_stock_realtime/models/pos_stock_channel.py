# -*- coding: utf-8 -*-

from odoo import api, fields, models
from collections import deque


class PosStockChannel(models.TransientModel):
    _name = 'pos.stock.channel'

    def broadcast(self, stock_quant):
        data = stock_quant.read(['product_id', 'location_id', 'quantity'])
        self.env['bus.bus'].sendone((self._cr.dbname, 'pos.stock.channel'), data)
