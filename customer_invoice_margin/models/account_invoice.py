# -*- coding: utf-8 -*-
#################################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2018-today Ascetic Business Solution <www.asceticbs.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#################################################################################

from odoo import api, models, fields

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    margin_amount = fields.Char(compute='_get_average_margin_percentage', string='Margin Amount')
    margin_percentage = fields.Char(compute='_get_average_margin_percentage', string='Margin Percentage')

    @api.one
    @api.depends('invoice_line_ids','invoice_line_ids.quantity','invoice_line_ids.price_unit', 'invoice_line_ids.discount')
    def _get_average_margin_percentage(self):
        sale_price = discount = cost = margin_amount = 0.0
        line_cost = line_margin_amount = margin_percentage = 0.0
        for record in self:
            if record.invoice_line_ids:
                for line in record.invoice_line_ids:
                    sale_price = line.price_unit * line.quantity
                    discount = (sale_price * line.discount)/100
                    cost = line.product_id.standard_price * line.quantity
                    line_cost += cost
                    margin_amount = (sale_price - discount) - cost
                    line_margin_amount += margin_amount
                if line_cost:
                    margin_percentage = (line_margin_amount / line_cost) * 100
                else:
                    margin_percentage = 100
                record.margin_amount = line_margin_amount
                record.margin_percentage = str(round(margin_percentage,2)) + '%'

class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    margin_percentage = fields.Char(compute='_get_total_percentage', string='Margin Percentage')

    @api.one
    @api.depends('quantity','price_unit', 'discount')
    def _get_total_percentage(self):
        sale_price = discount = cost = margin_amount = margin_percentage = 0.0
        for record in self:
            if record.product_id:
                sale_price = record.price_unit * record.quantity
                discount = (sale_price*record.discount)/100
                cost = record.product_id.standard_price * record.quantity
                margin_amount = (sale_price - discount) - cost
                if cost:
                    margin_percentage = (margin_amount / cost) * 100 
                else:
                    margin_percentage = 100 
                record.margin_percentage = str(round(margin_percentage,2)) + ' %'
