# -*- coding: utf-8 -*-
# Copyright 2013-15 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright 2015-2016 AvanzOSC
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    invoice_line_ids = fields.Many2many(
        comodel_name='account.invoice.line', string='Invoice Line', readonly=True,
        copy=False)