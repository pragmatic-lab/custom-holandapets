from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.tools.float_utils import float_compare
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF, DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.exceptions import UserError, ValidationError

STATES = {'draft': [('readonly', False),]}

class StockPicking(models.Model):

    _inherit = 'stock.picking'
    
    @api.depends('date_movement','state')
    def _compute_message_moves_future(self):
        move_model = self.env['stock.move']
        message_moves_future = []
        product_data = {}
        for picking in self.filtered('date_movement'):
            message_moves_future = []
            product_data = {}
            for move in picking.move_lines:
                moves_future = move_model.search([
                    ('product_id','=',move.product_id.id),
                    ('state','=','done'),
                    ('date','>=',picking.date_movement),
                    ('id', 'not in', picking.move_lines.ids)                              
                ])
                if moves_future:
                    product_data.setdefault(move.product_id, []).extend(moves_future.ids)
            if product_data:
                date_move = fields.Datetime.context_timestamp(picking, picking.date_movement)
                message_moves_future.append("<h5 style='color: red;'>ADVERTENCIA</h5>")
                message_moves_future.append("Con la fecha de inventario: %s los siguientes productos: <br/>" % fields.Datetime.to_string(date_move))
                message_moves_future.append("<ul>")
                for product in product_data:
                    message_moves_future.append("<li>%s</li>" % product.display_name)
                message_moves_future.append("</ul>")
                message_moves_future.append("Tienen movimientos posteriores y posiblemente necesiten reproceso de costo")
                message_moves_future = "".join(message_moves_future)
            picking.message_moves_future = "".join(message_moves_future) if message_moves_future else False
    
    #reemplazo de campos para modificar el readonly y states
    origin = fields.Char(readonly=True, states=STATES)
    date = fields.Datetime(readonly=True, states=STATES)
    picking_type_id = fields.Many2one('stock.picking.type', readonly=True, states=STATES,)
    partner_id = fields.Many2one('res.partner', readonly=True, states=STATES,)
    #campo para configurar la fecha del movimiento de stock, para que esta fecha se pase a los quants
    date_movement = fields.Datetime('Fecha de Inventario', copy=False,
        readonly=False, states={'done': [('readonly', True),], 'cancel': [('readonly', True),]}, 
        help="Especifica la fecha en la que se movera el inventario.\n"\
            "Asigne una fecha cuando desea mover inventario en fechas pasadas, deje vacio para tomar la fecha actual",)
    message_moves_future = fields.Html('Movimientos Futuros despues de fecha de movimiento',
        compute='_compute_message_moves_future', store=True)
    
    @api.constrains('date_movement',)
    def _check_date_movement(self):
        for picking in self:
            #no permitir especificar una fecha mayor a la fecha actual
            #esto haria que falle el reporte de inventario a la fecha
            #ademas si es algo en el futuro, debe procesarse el dia q le toque, no antes
            if picking.date_movement and picking.date_movement > fields.Datetime.now():
                raise ValidationError("No puede especificar una fecha de inventario mayor a la fecha actual, por favor verifique el picking: %s" % picking.name)
    
    @api.multi
    def action_cancel_backorder(self):
        """
        Cancelar la recepcion parcial previa
        """
        picking_vals = {}
        for picking in self:
            if picking.picking_type_code != 'incoming' or not picking.backorder_id:
                continue
            #enviar a cancelar el picking anterior
            backorder = picking.backorder_id
            backorder.action_cancel()
            backorder.move_lines.write({
                'picking_id': picking.id,
                'state': 'draft',
            })
            picking.do_unreserve()
            picking.move_lines._merge_moves()
            #cambiar el name y el backorder del picking actual, para tomar los del picking anterior
            #hay una restriccion que el nombre del picking sea unico por compañia
            #por ello pasar el nombre a una variable temporal y borrar el nombre del backorder
            picking_vals = {
                'name': backorder.name,
                'backorder_id': backorder.backorder_id and backorder.backorder_id.id or False,
            }
            backorder.unlink()
            picking.write(picking_vals)
            picking.action_assign()
        return True
    
    @api.multi
    def action_done(self):
        ctx = self.env.context.copy()
        for picking in self:
            ctx = self.env.context.copy()
            #si el picking tiene lleno el campo
            #pasar eso para que los movimientos y quants se asienten con esa fecha
            if picking.date_movement:
                ctx['date_for_move'] = picking.date_movement
            super(StockPicking, picking.with_context(ctx)).action_done()
            #los movimientos de stock que no se procesaro y se pasaron a una backorder
            #restaurar la fecha prevista del picking
            if picking.date_movement:
                backorder = self.search([('backorder_id','=',picking.id)])
                if backorder:
                    backorder.move_lines.write({'date': picking.date})
        return True    
    
    @api.multi
    def unlink(self):
        for picking in self:
            if picking.state in ('done', 'assigned'):
                raise UserError("No puede eliminar este registro, intente cancelarlo primero")
        return super(StockPicking, self).unlink()
    
    @api.multi
    def _get_report_base_filename(self):
        self.ensure_one()
        report_name = "Recepción %s" % self.name
        if self.picking_type_code == 'internal':
            report_name = "Transferencia %s" % self.name
        if self.picking_type_code == 'outgoing':
            report_name = "Despacho %s" % self.name
        return report_name
