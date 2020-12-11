# -*- coding: utf-8 -*-

from odoo import api, fields, models
from collections import deque


class PosConfig(models.Model):
    _inherit = 'pos.config'

    show_qty_available = fields.Boolean(
        string='Display Stock in POS',
        help="Apply show quantity of POS",
        default=True
    )
    location_only = fields.Boolean(
        string='Count only for POS Location',
        help='Only show product quantities in stock location of this POS')
    allow_out_of_stock = fields.Boolean(
        string='Allow Out-of-Stock')
    limit_qty = fields.Integer(
        string='Deny Order when available quantity is lower than')
    hide_product = fields.Boolean(
        string='Hide Products which are not in POS Location',
        help='Hide products with negative stocks or not exist in the stock location of this POS'
    )
