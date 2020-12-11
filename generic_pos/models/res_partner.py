from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    @api.multi
    def write(self, values):
        if 'active' in values and not values.get('active'):
            sessions_opened = self.env['pos.session'].sudo().search_count([
                ('state', '!=', 'closed'),
            ])
            if sessions_opened > 0 and not self.env['ir.module.module'].sudo().search([('name', '=', 'pos_speed_up'), ('state', '=', 'installed')], limit=1):
                raise UserError('No puede inactivar un cliente mientras haya sessiones abiertas en el punto de venta')
        res = super(ResPartner, self).write(values)
        return res