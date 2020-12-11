# Copyright 2018 Dinar Gabbasov <https://it-projects.info/team/GabbasovDinar>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import models, api, fields, tools, _
from odoo.tools import float_is_zero
import psycopg2
import logging

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    returned_order = fields.Boolean('Returned Order', default=False)
    origin_order_id = fields.Many2one('pos.order', 
        'Pedido Original', readonly=True, copy=False)
    devolution_ids = fields.One2many('pos.order', 'origin_order_id',
        'Devoluciones', readonly=True, copy=False)
    
    @api.model
    def create(self, vals):
        new_order = super(PosOrder, self).create(vals)
        # cuando tiene un pedido de origen es una devolucion
        # verificar si hay lineas que no tienen linea de origen
        # y pasarle la linea de origen en base al producto
        if new_order.origin_order_id:
            for line in new_order.lines:
                if line.line_origin_id:
                    continue
                line_origin = new_order.origin_order_id.lines.filtered(lambda x: x.product_id == line.product_id)
                if line_origin:
                    line.line_origin_id = line_origin[0].id
        return new_order
    
    @api.multi
    def _prepare_refund(self, current_session):
        vals = super(PosOrder, self)._prepare_refund(current_session)
        vals['origin_order_id'] = self.id
        vals['returned_order'] = True #compatibilidad con pos_order_history_return
        return vals
    
    @api.model
    def create_from_ui(self, orders):
        # Keep return orders
        submitted_references = [o['data']['name'] for o in orders]
        pos_order = self.search([('pos_reference', 'in', submitted_references)])
        existing_orders = pos_order.read(['pos_reference'])
        existing_references = set([o['pos_reference'] for o in existing_orders])
        orders_to_save = [o for o in orders if o['data']['name'] in existing_references and o['data'].get('return_lines')]

        self.return_from_ui(orders_to_save)

        return super(PosOrder, self).create_from_ui(orders)

    @api.multi
    def return_from_ui(self, orders):
        for tmp_order in orders:
            to_invoice = tmp_order['to_invoice']
            order = tmp_order['data']
            if to_invoice:
                self._match_payment_to_invoice(order)

            order['returned_order'] = True
            pos_order = self._process_order(order)

            try:
                pos_order.action_pos_order_paid()
            except psycopg2.OperationalError:
                raise
            except Exception as e:
                _logger.error('Could not fully process the POS Order: %s', tools.ustr(e))
                raise

            if to_invoice:
                pos_order.action_pos_order_invoice()
                pos_order.invoice_id.sudo().action_invoice_open()
                pos_order.account_move = pos_order.invoice_id.move_id
    
    @api.model
    def _order_fields(self, ui_order):
        order_vals = super(PosOrder, self)._order_fields(ui_order)
        if ui_order.get('returned_order'):
            order_vals['returned_order'] = True
        return_data_aditional = ui_order.get('return_data_aditional')
        # return_data_aditional es un diccionario creado en JS con valores adicionales a pasar al backend
        # solo tomar los campos que existan en pos.order para evitar procesar campos que no existan
        # pasar las referencias a la NC en base al pedido original
        if ui_order.get('origin_order_id'):
            order_vals['origin_order_id'] = ui_order['origin_order_id']
            if return_data_aditional:
                for field_name in return_data_aditional:
                    if field_name in self._fields:
                        order_vals[field_name] = return_data_aditional[field_name]
        return order_vals


class PosOrderLine(models.Model):

    _inherit = 'pos.order.line'
    
    line_origin_id = fields.Many2one('pos.order.line', u'Linea Original', index=True, copy=False)

    @api.multi
    def _prepare_refund_line(self, new_order):
        vals = super(PosOrderLine, self)._prepare_refund_line(new_order)
        vals['line_origin_id'] = self.id
        return  vals
