# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

from odoo import fields, models, api, _
from datetime import datetime, timedelta
from odoo.exceptions import Warning
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
import time
from pytz import timezone
from odoo.exceptions import UserError,ValidationError
from odoo.tools import float_is_zero

class PosOrder(models.Model):
    _inherit = "pos.order"

    salesman_id = fields.Many2one('res.users',string='Salesman')
    is_draft_order = fields.Boolean(u'Es Pedido en Borrador?', copy=False)
    
    @api.multi
    def _is_valid_for_draft(self):
        return True

    @api.model
    def create(self, values):
        order_id = super(PosOrder, self).create(values)
        if order_id.user_id.pos_user_type != 'cashier' and order_id.is_draft_order and order_id._is_valid_for_draft():
            notifications = []
            cashiers = self.env['res.users'].search([('sales_persons', '!=', False)])
            for user in cashiers:
                for salesperson in user.sales_persons:
                    if salesperson.id == order_id.salesman_id.id:
                        session = self.env['pos.session'].search([
                            ('user_id', '=', user.id),
                            ('state', '=', 'opened'),
                        ], limit=1)
                        if session:
                            notifications.append([(self._cr.dbname, 'sale.note', user.id), {'new_pos_order': order_id.read()}])
            if notifications:
                self.env['bus.bus'].sendmany(notifications)
        return order_id

    def _order_fields(self,ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        res.update({
            'salesman_id': ui_order.get('salesman_id') or False,
            'is_draft_order': ui_order.get('is_draft_order') or False,
        });
        return res

    @api.multi
    def unlink(self):
        for order in self:
            if order.salesman_id and order.config_id.enable_reorder:
                notifications = []
                notify_users = []
                # si el q elimina el pedido no es el vendedor
                # notificar al vendedor
                if self._uid != order.salesman_id.id:
                    notify_users.append(order.salesman_id.id)
                # buscar los cajeros que son responsables de ese vendedor y notificarlos
                cashiers = self.env['res.users'].search([('sales_persons', '!=', False)])
                for user in cashiers:
                    for salesperson in user.sales_persons:
                        if salesperson.id == order.salesman_id.id:
                            session = self.env['pos.session'].search([
                                ('user_id','=',user.id),
                                ('state', '=', 'opened'),
                            ], limit=1)
                            if session:
                                notify_users.append(session.user_id.id)
                for user in notify_users:
                    notifications.append([(self._cr.dbname, 'sale.note', user), {'cancelled_sale_note': self.read()}])
                self.env['bus.bus'].sendmany(notifications)
        return super(PosOrder, self).unlink()

    @api.multi
    def action_pos_order_paid(self): 
        order_draft = self.filtered(lambda x: x.is_draft_order and x.state == 'draft' and not x.statement_ids)
        res = super(PosOrder, self-order_draft).action_pos_order_paid()
        for order in self:
            # solo notificar si el pedido era un pedido en borrador creado asi desde el pos
            # cuando se tiene instalado el modulo pero no esta habilitado en el pos
            # no se deberia notificar por gusto
            if not order.config_id.enable_reorder:
                continue
            if not order._is_valid_for_draft():
                continue
            notifications = []
            notify_users = []
            if order.salesman_id:
                notify_users.append(order.salesman_id.id)
            cashiers = self.env['res.users'].search([('sales_persons', '!=', False)])
            for user in cashiers:
                for salesperson in user.sales_persons:
                    if salesperson.id == order.salesman_id.id:
                        session = self.env['pos.session'].search([
                            ('user_id','=',user.id),
                            ('state', '=', 'opened'),
                        ], limit=1)
                        if session:
                            notify_users.append(session.user_id.id)
            if len(notify_users) > 0:
                for user in notify_users:
                    notifications.append([(self._cr.dbname, 'sale.note', user), {'new_pos_order': order.read()}])
                self.env['bus.bus'].sendmany(notifications)
        return res
    
    @api.model
    def create_from_ui(self, orders):
        # filtrar los pedidos que estaban en borrador pero ya se pagaron para no volver a procesarlos
        submitted_references = [o['data']['old_order_id'] for o in orders if o['data'].get('old_order_id')]
        pos_order_ids = self.search([('id', 'in', submitted_references), ('state', '!=', 'draft')]).ids
        orders_to_save = [o for o in orders if o['data'].get('old_order_id') not in pos_order_ids]
        return super(PosOrder, self).create_from_ui(orders_to_save)

    @api.model
    def _process_order(self,order):
        draft_order_id = order.get('old_order_id')
        if not order.get('draft_order') and draft_order_id:
            order_id = draft_order_id
            order_obj = self.browse(order_id)
            prec_acc = order_obj.pricelist_id.currency_id.decimal_places
            if order_obj.lines:
                order_obj.lines.unlink()
            temp = self._order_fields(order)
            temp.pop('statement_ids', None)
            temp.pop('name', None)
            temp.update({
                'date_order': order.get('creation_date'),
                'session_id': order.get('pos_session_id'),
            })
            order_obj.write(temp)
            journal_ids = set()
            if not order_obj.statement_ids:
                for payments in order['statement_ids']:
                    if not float_is_zero(payments[2]['amount'], precision_digits=prec_acc):


                        vals = self._payment_fields(payments[2])
                        vals['amount'] = vals['amount'] -order['amount_return']
                        order_obj.add_payment(vals)
                    	 #order_obj.add_payment(self._payment_fields(payments[2]))

                    journal_ids.add(payments[2]['journal_id'])

                session = self.env['pos.session'].browse(order['pos_session_id'])
                if session.sequence_number <= order['sequence_number']:
                    session.write({'sequence_number': order['sequence_number'] + 1})
                    session.refresh()
    
                if not float_is_zero(order['amount_return'], prec_acc):
                    cash_journal_id = session.cash_journal_id.id
                    if not cash_journal_id:
                        # Select for change one of the cash journals used in this
                        # payment
                        cash_journal = self.env['account.journal'].search([
                            ('type', '=', 'cash'),
                            ('id', 'in', list(journal_ids)),
                        ], limit=1)
                        if not cash_journal:
                            # If none, select for change one of the cash journals of the POS
                            # This is used for example when a customer pays by credit card
                            # an amount higher than total amount of the order and gets cash back
                            cash_journal = [statement.journal_id for statement in session.statement_ids if statement.journal_id.type == 'cash']
                            if not cash_journal:
                                raise UserError(_("No cash statement found for this session. Unable to record returned cash."))
                        cash_journal_id = cash_journal[0].id
                    #order_obj.add_payment({
                    #    'amount': -order['amount_return'],
                    #    'payment_date': fields.Date.context_today(self),
                    #    'payment_name': _('return'),
                    #    'journal': cash_journal_id,
                    #})
                if order_obj.rounding:
                    rounding_journal_id = order_obj.session_id.config_id.rounding_journal_id
                    if rounding_journal_id:
                        order_obj.add_payment({
                            'amount': order_obj.rounding * -1,
                            'payment_name': 'Redondeo',
                            'journal': rounding_journal_id.id,
                        })
            return order_obj
        if not order.get('draft_order') and not draft_order_id:
            order_id = super(PosOrder, self)._process_order(order)
            return order_id

    @api.model
    def ac_pos_search_read(self, domain):
        domain = domain.get('domain')
        search_vals = self.search_read(domain)
        user_id = self.env['res.users'].browse(self._uid)
        tz = False
        result = []
        if self._context and self._context.get('tz'):
            tz = timezone(self._context.get('tz'))
        elif user_id and user_id.tz:
            tz = timezone(user_id.tz)
        if tz:
            c_time = datetime.now(tz)
            hour_tz = int(str(c_time)[-5:][:2])
            min_tz = int(str(c_time)[-5:][3:])
            sign = str(c_time)[-6][:1]
            for val in search_vals:
                date_order = fields.Date.from_string(str(val.get('date_order')))
                date_new_order = datetime.strftime(date_order, DEFAULT_SERVER_DATETIME_FORMAT)
                if sign == '-':
                    val.update({
                        'date_order':(val.get('date_order') - timedelta(hours=hour_tz, minutes=min_tz)).strftime('%Y-%m-%d %H:%M:%S')
                    })
                elif sign == '+':
                    val.update({
                        'date_order':(val.get('date_order') + timedelta(hours=hour_tz, minutes=min_tz)).strftime('%Y-%m-%d %H:%M:%S')
                    })
                result.append(val)
            return result
        else:
            return search_vals


class pos_config(models.Model):
    _inherit = "pos.config"

    enable_reorder = fields.Boolean("Order Sync")
    enable_operation_restrict = fields.Boolean("Operation Restrict")
    pos_managers_ids = fields.Many2many('res.users','posconfig_partner_rel','location_id','partner_id', string='Managers')
    enable_order_merge = fields.Boolean(string="Unificar Pedidos en borrador?", default=False)
    enable_pedidos_list = fields.Boolean(string="Mostrar Listado de Pedidos?", default=True)


class ResUsers(models.Model):
    _inherit = 'res.users'

    pos_user_type = fields.Selection([('cashier','Cashier'),('salesman','Sales Person')],string="POS User Type",default='salesman')
    can_give_discount = fields.Boolean("Can Give Discount")
    can_change_price = fields.Boolean("Can Change Price")
    discount_limit = fields.Float("Discount Limit")
    based_on = fields.Selection([('pin','Pin'),('barcode','Barcode')],
                                   default='barcode',string="Authenticaion Based On")
    sales_persons = fields.Many2many('res.users','sales_person_rel','sales_person_id','user_id', string='Sales Person')

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if self._context.get('from_sales_person'):
            users = []
            pos_users_ids = self.env.ref('point_of_sale.group_pos_user').users.ids
            sale_person_ids = self.search([('id', 'in', pos_users_ids),
                                           ('pos_user_type', '=', 'salesman')])
            selected_sales_persons = []
            for user in pos_users_ids:
                user_id = self.browse(user)
                if user_id.sales_persons:
                    selected_sales_persons.append(user_id.sales_persons.ids)
            if sale_person_ids:
                users.append(sale_person_ids.ids)
            if users:
                args += [['id', 'in', users[0]]]
#             if selected_sales_persons:
#                 args += [['id', 'not in', selected_sales_persons[0]]]
        return super(ResUsers, self).name_search(name, args=args, operator=operator, limit=limit)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
