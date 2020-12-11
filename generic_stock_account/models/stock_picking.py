from odoo import models, api, fields
from odoo.tools.float_utils import float_is_zero
from odoo.exceptions import UserError, ValidationError

STATES = {'draft': [('readonly', False),]}


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    has_account_move = fields.Boolean(
        'Tiene Asientos contables', compute='_compute_has_account_move')

    def _compute_has_account_move(self):
        for picking in self:
            picking.has_account_move = any(m.account_move_ids for m in picking.move_lines)
            
    @api.multi
    def action_see_account_move(self):
        self.ensure_one()
        action_ref = self.env.ref('account.action_move_journal_line')
        if not action_ref:
            return False
        action_data = action_ref.read()[0]
        action_data['domain'] = [('id', 'in', self.move_lines.mapped('account_move_ids').ids)]
        return action_data
