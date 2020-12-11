from odoo import models, api, fields
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round


class StockMove(models.Model):
    _inherit = 'stock.move'
    
    @api.model
    def _get_in_base_domain(self, company_id=False):
        # Domain:
        # - state is done
        # - coming from a location without company, or an inventory location within the same company
        # - going to a location within the same company
        domain = [
            ('state', '=', 'done'),
            '&',
                '|',
                    ('location_id.company_id', '=', False),
                    '&',
                        # agregar transit para cuando se hagan transferencias internas se pueda valorar el producto resultante(en ventas)
                        # caso contrario se mueve el producto sin problemas, pero no toma el costo correctamente y tomara el precio promedio
                        ('location_id.usage', 'in', ['inventory', 'production', 'transit']),
                        ('location_id.company_id', '=', company_id or self.env.user.company_id.id),
                ('location_dest_id.company_id', '=', company_id or self.env.user.company_id.id),
        ]
        return domain
    
    @api.multi
    def _is_transfer(self):
        self.ensure_one()
        # transferencias internas en 2 pasos van de una bodega interna a la bodega de transferencia entre company
        # o viceversa
        return self._is_transfer_in() or self._is_transfer_out()
            
    @api.multi
    def _is_transfer_in(self):
        # es entrada de transferencia cuando sale de la bodega de transferencia y va a la bodega de stock
        self.ensure_one()
        return (self.location_id.usage == 'transit' and self.location_dest_id.usage == 'internal')
            
    @api.multi
    def _is_transfer_out(self):
        # es salida de transferencia cuando sale de la bodega de stock a la bodega de transferencia
        self.ensure_one()
        return (self.location_id.usage == 'internal' and self.location_dest_id.usage == 'transit')
    
    # @override
    @api.multi
    def _run_valuation(self, quantity=None):
        # Extend `_run_valuation` to make it work on internal moves.
        res = super(StockMove, self)._run_valuation(quantity)
        if self._is_transfer() and not self.value:
            if self._is_transfer_in():
                valued_quantity = 0
                for valued_move_line in self.move_line_ids:
                    valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done, self.product_id.uom_id)
    
                # Note: we always compute the fifo `remaining_value` and `remaining_qty` fields no
                # matter which cost method is set, to ease the switching of cost method.
                vals = {}
                price_unit = self._get_price_unit()
                value = price_unit * (quantity or valued_quantity)
                value_to_return = value if quantity is None or not self.value else self.value
                vals = {
                    'price_unit': price_unit,
                    'value': value_to_return,
                    'remaining_value': value if quantity is None else self.remaining_value + value,
                }
                vals['remaining_qty'] = valued_quantity if quantity is None else self.remaining_qty + quantity
    
                if self.product_id.cost_method == 'standard':
                    value = self.product_id.standard_price * (quantity or valued_quantity)
                    value_to_return = value if quantity is None or not self.value else self.value
                    vals.update({
                        'price_unit': self.product_id.standard_price,
                        'value': value_to_return,
                    })
                self.write(vals)
            else:
                valued_quantity = 0
                for valued_move_line in self.move_line_ids:
                    valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done, self.product_id.uom_id)
                self.env['stock.move']._run_fifo(self, quantity=valued_quantity)
                if self.product_id.cost_method in ['standard', 'average']:
                    curr_rounding = self.company_id.currency_id.rounding
                    value = -float_round(self.product_id.standard_price * (valued_quantity if quantity is None else quantity), precision_rounding=curr_rounding)
                    value_to_return = value if quantity is None else self.value + value
                    self.write({
                        'value': value_to_return,
                        'price_unit': value / valued_quantity,
                    })
        return res

    @api.multi
    def cancel_account_move(self):
        for move in self.sudo():
            am_posted = move.account_move_ids.filtered(lambda x: x.state == 'posted')
            if am_posted:
                am_posted.button_cancel()
            move.account_move_ids.unlink()
        return True
      
    @api.multi
    def _action_cancel(self):
        if not self.env.context.get('dont_unlink_am', False):
            self.cancel_account_move()
        return super(StockMove, self)._action_cancel()
    
    # @override
    @api.multi
    def _action_done(self):
        """Call _account_entry_move for internal moves as well."""
        res = super(StockMove, self)._action_done()
        if not self.env.context.get('force_transfer_create_account_move'):
            return res
        for move in res:
            # first of all, define if we need to even valuate something
            if move.product_id.valuation != 'real_time':
                continue
            # we're customizing behavior on moves between internal locations
            # only, thus ensuring that we don't clash w/ account moves
            # created in `stock_account`
            if not move._is_transfer():
                continue
            move._account_entry_move()
        return res

    # @override
    def _account_entry_move(self):
        """
        Accounting Valuation Entries
        """
        if self.env.context.get('skip_valuation_moves'):
            return False
        res = super(StockMove, self)._account_entry_move()
        if res is not None and not res:
            # `super()` tends to `return False` as an indicator that no
            # valuation should happen in this case
            return res

        # get valuation accounts for product
        if self._is_transfer():
            # treated by `super()` as a self w/ negative qty due to this hunk:
            # quantity = self.product_qty or context.get('forced_quantity')
            # quantity = quantity if self._is_in() else -quantity
            # so, self qty is flipped twice and thus preserved
            self = self.with_context(forced_quantity=-self.product_qty)
            journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
            if self._is_transfer_out():
                self._create_account_move_line(acc_valuation, acc_dest, journal_id)
            else:
                self._create_account_move_line(acc_dest, acc_valuation, journal_id)
        return res

    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id):
        if self.env.context.get('skip_valuation_moves'):
            return []
        if not self._context.get('force_period_date') and self.date:
            #tomar la fecha del movimiento de stock
            date = fields.Datetime.context_timestamp(self, self.date)
            super(StockMove, self.with_context(force_period_date=date))._create_account_move_line(credit_account_id, debit_account_id, journal_id)
        else:
            super(StockMove, self)._create_account_move_line(credit_account_id, debit_account_id, journal_id)
            
    @api.multi
    def _get_price_valuation(self, product):
        # obtener la valoracion del stock
        # se verifico que en cualquier metodo de costo(estandar, promedio, FIFO)
        # el sistema siempre guarda el valor correcto en el campo value
        # pero para efectos practicos devolver el precio unitario
        # que tambien se verifico y siempre es correcto(value/product_qty)
        # solo en caso de necesitar algo diferente sobreescribir esta funcion
        price_valuation = 0.0
        for move in self.filtered(lambda x: x.product_id == product):
            price_valuation = move.price_unit
        return price_valuation

