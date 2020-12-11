from collections import OrderedDict

from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class StockMove(models.Model):
    _inherit = 'stock.move'
    
    @api.one
    @api.depends('product_id', 'product_uom_qty', 'product_uom', 'price_unit')
    def _compute_price_uom_unit(self):
        #calcular el precio que esta en la UdM del producto a la UdM del movimiento de stock
        if self.product_uom:
            self.price_uom_unit = self.product_id.uom_id._compute_price(self.price_unit, self.product_uom)
        
    @api.one
    @api.depends('product_id', 'product_uom_qty', 'product_uom','price_uom_unit')
    def _compute_price_subtotal(self):
        self.price_subtotal = (self.price_uom_unit and self.price_uom_unit or 0.0) * self.product_uom_qty
    
    price_uom_unit = fields.Float('Costo Unitario', digits=dp.get_precision('Product Price'), 
        compute='_compute_price_uom_unit', store=True,
        help="Precio Unitario en base a la UdM del movimiento",)
    price_subtotal = fields.Float('Subtotal Costo', digits=dp.get_precision('Account'), 
        compute='_compute_price_subtotal', store=False, help="",)
    
    @api.onchange('product_id')
    def onchange_product_id(self):
        res = super(StockMove, self).onchange_product_id()
        if self.product_id:
            self.price_unit = self.product_id.standard_price
        return res
    
    @api.multi
    def _action_done(self):
        company = self.env.user.company_id
        if company.stock_policy == 'control_stock' or self.env.context.get('force_validation_stock'):
            #si el movimiento proviene desde una bodega interna, 
            #se debe tener el suficiente stock para procesar el movimiento
            #para evitar tener stock negativo
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            Quant = self.env['stock.quant']
            qty_available_per_product, qty_per_product = {}, {}
            product_key = False
            available_qty = 0.0
            product_uom_name, message_prodlot = "", ""
            messaje_list = []
            default_line = {
                'qty_done': 0,
                'product_qty': 0,
            }
            for move in self.filtered(lambda x: x.location_id.usage == 'internal' and x.product_id.type == 'product'):
                product_uom_name = move.product_id.uom_id.name
                move_line_data = OrderedDict()
                for ml in move.move_line_ids:
                    product_key = (ml.product_id, ml.location_id, ml.lot_id, ml.package_id, ml.owner_id)
                    move_line_data.setdefault(product_key, default_line.copy())
                    move_line_data[product_key]['qty_done'] += ml.qty_done
                    move_line_data[product_key]['product_qty'] += ml.product_qty
                for product_key, values in move_line_data.items():
                    product, location, lot, package, owner = product_key
                    #cuando esta todo reservado, no validar disponibilidad de stock
                    if float_compare(values['product_qty'], values['qty_done'], precision_digits=precision) >= 0:
                        continue
                    qty_need = values['qty_done'] - values['product_qty']
                    message_prodlot = ""
                    #calcular las cantidades disponibles del producto una sola vez
                    #ya que no va a variar la cantidad disponible mientras no se asiente el movimiento
                    #esto es util cuando tengo varios movimientos de stock con el mismo producto
                    if product_key not in qty_available_per_product:
                        available_qty = Quant._get_available_quantity(product, location, 
                                                                  lot_id=lot, package_id=package, owner_id=owner, strict=True)
                        qty_available_per_product[product_key] = available_qty
                        if lot:
                            message_prodlot = " con el lote de producción %s" % lot.display_name
                    else:
                        available_qty = qty_available_per_product[product_key]
                    #ir acumulando las cantidades por producto y bodega, en caso que hayan varios movimientos del mismo producto
                    #ejemplo, paso dos movimientos con el producto 1
                    #producto 1 tiene en stock 100 unidades
                    #movimiento 1 es de 50 unidades
                    #movimiento 2 es de 60 unidades
                    #la sumatoria es 110 unidades que pasa lo disponible del producto
                    #evaluando unitariamente 50 y luego 60, nunca saldra que no tiene stock
                    #pero si acumulo las cantidades, el segundo movimiento no se permitira
                    qty_per_product.setdefault(product_key, 0.0)
                    available_qty -= qty_per_product.get(product_key, 0.0)
                    if float_compare(available_qty, qty_need, precision_digits=precision) < 0:
                        messaje_list.append('No se puede procesar el producto %s, no hay stock disponible en la bodega %s %s, ' \
                                            'requiere %s %s, hay disponible %s %s y tiene reservado %s %s, %s %s Movidas previamente' \
                                            % (product.display_name, location.display_name, message_prodlot, 
                                               values['qty_done'], product_uom_name, available_qty, product_uom_name, values['product_qty'], product_uom_name,
                                               qty_per_product[product_key], product_uom_name))
                    qty_per_product[product_key] += values['qty_done']
            if messaje_list and not self.env.context.get('force_stock_move', False):
                raise UserError("\n".join(messaje_list))
        moves_todo = super(StockMove, self)._action_done()
        moves_todo._action_propagate_valuation()
        return moves_todo
    
    @api.multi
    def _action_propagate_valuation(self):
        # esta funcion se debe usar en ventas, pos, etc para recalcular el costo de venta de cada linea del pedido
        return True
    
    @api.multi
    def _action_cancel(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        Quant = self.env['stock.quant']
        PriceHistory = self.env['product.price.history']
        company = self.env.user.company_id
        if company.stock_policy == 'control_stock' or self.env.context.get('force_validation_stock'):
            for move in self.filtered(lambda x: x.state == 'done'):
                #cuando la bodega destino es tipo interno, solo permitir cancelar si hay suficiente stock
                #esto para evitar devolver si no hay stock suficiente xq ya se uso ese stock
                if move.location_dest_id.usage == 'internal':
                    for ml in move.move_line_ids:
                        available_qty = Quant._get_available_quantity(ml.product_id, ml.location_dest_id, 
                                                                      lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                        qty_done = ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id)
                        if float_compare(available_qty, qty_done, precision_digits=precision) < 0:
                            raise UserError("No puede cancelar el movimiento de stock: %s, el producto: %s ya ha sido usado, por favor verifique" % 
                                            (move.display_name, move.product_id.display_name))
        #restar la cantidad realizada
        for move in self.filtered(lambda x: x.state == 'done'):
            for ml in move.move_line_ids:
                #restar la cantidad de la bodega destino
                qty_done = ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id)
                available_qty, in_date = Quant._update_available_quantity(ml.product_id, ml.location_dest_id, -qty_done, 
                                                                          lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
                #hacer el reingreso del stock a la bodega origen
                available_qty, in_date = Quant._update_available_quantity(ml.product_id, ml.location_id, qty_done, 
                                                                          lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
                # FIXME:
                # cuando se usa valoraion FIFO, se usan los campos remaining_qty y remaining_value
                # al cancelar esos campos se deberian volver a sumar al movimiento origen del que se restaron
                # pero estructuralmente no hay como saber de que movimiento origen se restaron cuando se valido este movimiento
                # por ello tener cuidado en las cancelaciones de algo ya realizado
            move.write({'state': 'assigned'})
        for move in self.filtered(lambda x: x.origin and x.state != 'cancel'):
            #buscar los precios historicos que se crearon con el origen del movimiento y eliminarlos
            price_history_recs = PriceHistory.search([
                ('product_id', '=', move.product_id.id),
                ('company_id', '=', company.id),
                ('reason', '=', "%s_%s" % (move.origin or '', move.id)),
                ])
            if price_history_recs:
                price_history_recs.sudo().unlink()
            #tomar el ultimo precio y ese pasarlo al precio del producto
            if move.product_id.cost_method == 'average':
                price_history_recs = PriceHistory.search([
                    ('product_id', '=', move.product_id.id),
                    ('company_id', '=', company.id),
                    ('cost', '!=', 0),
                    ], order='datetime DESC', limit=1)
                if price_history_recs:
                    cost_reason = "Cancelacion de %s_%s" % (move.origin or '', move.id)
                    move.product_id.sudo().with_context(save_cost_reason=cost_reason).write({'standard_price': price_history_recs.cost})
        res = super(StockMove, self)._action_cancel()
        return res
    
    def _get_sequence_code_for_lot(self):
        return 'stock.lot.serial'
    
    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        #cuando este activa la opcion de crear lotes automaticamente crearlos
        #pasar el nombre del lote tomado desde la secuencia
        vals = super(StockMove, self)._prepare_move_line_vals(quantity, reserved_quant)
        if not vals.get('lot_id') and self.product_id.tracking in ('lot', 'serial') and self.picking_type_id.use_create_lots:
            #cuando no hay lote, pero se especifica un lote en el context
            #usar ese lote(en NC por devolucion)
            if self.env.context.get('specific_lot_id'):
                vals['lot_id'] = self.env.context.get('specific_lot_id')
            #cuando se pase que no cree lote, no crear(esto desde NC por devolucion)
            elif self.env.context.get('create_lot_automatic', True):
                vals['lot_name'] = self.env['ir.sequence'].next_by_code(self._get_sequence_code_for_lot())
        return vals
    
    @api.model
    def _run_fifo(self, move, quantity=None):
        move_origin = "%s_%s" % (move.origin or '', move.id)
        return super(StockMove, self)._run_fifo(move.with_context(save_cost_reason=move_origin), quantity)
    
    @api.model
    def _run_valuation(self, quantity=None):
        move_origin = "%s_%s" % (self.origin or '', self.id)
        return super(StockMove, self.with_context(save_cost_reason=move_origin))._run_valuation(quantity)
    