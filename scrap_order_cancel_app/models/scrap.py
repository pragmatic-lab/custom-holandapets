# -*- coding: utf-8 -*-

from odoo.exceptions import Warning
from odoo import models, fields, exceptions, api, _
import io
import tempfile
import binascii
import logging
_logger = logging.getLogger(__name__)
from odoo.tools.float_utils import float_compare, float_round, float_is_zero
from odoo.exceptions import UserError

class StockScrap(models.Model):
	_inherit = "stock.scrap"

	state = fields.Selection([
		('draft', 'Draft'),
		('done', 'Done'),
		('cancel','Cancel')], string='Status', default="draft")

	@api.multi
	def action_cancel_scrap(self):
		for scrap in self:
			scrap.move_id._action_cancel()
			scrap.write({'state': 'cancel'})
			for account in scrap.move_id.account_move_ids:
				account.write({'state':'draft'})
		return True

	@api.multi
	def action_set_to_draft(self):
		for scrap in self:
			scrap.write({'state': 'draft'})
		return True

class StockMove(models.Model):
	_inherit = 'stock.move'
	
	def _action_cancel(self):
		if self.user_has_groups('scrap_order_cancel_app.group_scrap_cancel'):
			for move in self:
				move._do_unreserve()
				siblings_states = (move.move_dest_ids.mapped('move_orig_ids') - move).mapped('state')
				if move.propagate:
					# only cancel the next move if all my siblings are also cancelled
					if all(state == 'cancel' for state in siblings_states):
						move.move_dest_ids._action_cancel()
				else:
					if all(state in ('done', 'cancel') for state in siblings_states):
						move.move_dest_ids.write({'procure_method': 'make_to_stock'})
						move.move_dest_ids.write({'move_orig_ids': [(3, move.id, 0)]})          
				if move.state == 'done':
					stock_move_id = self.env['stock.move'].sudo().search([('product_id','=',move.product_id.id),('reference','=',move.scrap_ids.name)])
					for move_id in stock_move_id:
						for line in move_id.move_line_ids:
							stock_quant_id = self.env['stock.quant'].sudo().search([('product_id','=',move.product_id.id),('location_id','=',line.location_id.id),('lot_id','=',line.lot_id.id)])
							if stock_quant_id:
								quant_qty = stock_quant_id[0].quantity
								stock_quant_id[0].quantity = quant_qty + move.product_uom_qty
				if move.account_move_ids:
					move.account_move_ids.filtered(lambda x: x.state == 'posted').sudo().button_cancel()
					move.account_move_ids.sudo().unlink()
				self.write({'state': 'cancel', 'move_orig_ids': [(5, 0, 0)]})

		else:
			if any(move.state == 'done' for move in self):
				raise UserError(_('You cannot cancel a stock move that has been set to \'Done\'.'))
			for move in self:
				if move.state == 'cancel':
					continue
				move._do_unreserve()
				siblings_states = (move.move_dest_ids.mapped('move_orig_ids') - move).mapped('state')
				if move.propagate:
					# only cancel the next move if all my siblings are also cancelled
					if all(state == 'cancel' for state in siblings_states):
						move.move_dest_ids.filtered(lambda m: m.state != 'done')._action_cancel()
				else:
					if all(state in ('done', 'cancel') for state in siblings_states):
						move.move_dest_ids.write({'procure_method': 'make_to_stock'})
						move.move_dest_ids.write({'move_orig_ids': [(3, move.id, 0)]})
						
			self.write({'state': 'cancel', 'move_orig_ids': [(5, 0, 0)]})
		return True
