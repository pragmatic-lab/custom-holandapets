from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError
from odoo import SUPERUSER_ID

SUPERADMIN_ID = 2

class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.multi
    def action_pos_session_closing_control(self):
        for session in self:
            if session.user_id != self.env.user and self.env.uid not in (SUPERUSER_ID, SUPERADMIN_ID):
                raise UserError("No puede cerrar esta sesion ya que no pertenece a su usuario, solo el usuario que abrio la sesion puede cerrarla")
        res = super(PosSession, self).action_pos_session_closing_control()
        return res

    @api.multi
    def unlink(self):
        for session in self:
            if session.state == 'opening_control':
                # FIX: cuando se intenta eliminar una session que esta en estado de control de apertura
                # no permite eliminar xq hay una restriccion de base cuando esta habilidado el control de efectivo
                # al eliminar la session envia a eliminar los statements y a su vez a recalcular valores
                # en este caso especifico no recalcular campos calculados
                return super(PosSession, self.with_context(recompute=False)).unlink()
            else:
                raise UserError("No puede eliminar una session a menos que este en estado: Control de apertura")
        return super(PosSession, self).unlink()
