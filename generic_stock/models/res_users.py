from odoo import models, api, fields, tools


class ResUsers(models.Model):
    _inherit = 'res.users'
    
    @api.model
    def get_all_warehouse(self, user_id=None):
        return self.env['stock.warehouse'].search([])
    
    @api.model
    def get_all_location(self, user_id=None):
        return self.env['stock.location'].search([('usage', '=', 'internal')])
    
    @api.model
    def get_all_picking_type(self, user_id=None):
        return self.env['stock.picking.type'].search([])
