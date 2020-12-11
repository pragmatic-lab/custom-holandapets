from odoo import fields, models, api

from odoo.addons.base.models.res_users import name_boolean_group, name_selection_groups

class ResUsers(models.Model):
    _inherit = 'res.users'

    allow_reprint = fields.Boolean('Allow Reprint', default=True)
    
    @api.model
    def create(self, vals):
        new_rec = super(ResUsers, self).create(vals)
        for user in new_rec:
            if user.share:
                continue
            group_reprint = self.env.ref('pos_orders_history_reprint.group_pos_reprint', False)
            if user.allow_reprint:
                if user not in group_reprint.users:
                    user.sudo().write({'groups_id': [(4, group_reprint.id)]})
            else:
                if user in group_reprint.users:
                    user.sudo().write({'groups_id': [(3, group_reprint.id)]})
        return new_rec
    
    @api.multi
    def write(self, vals):
        check_allow_reprint = True
        group_reprint = self.env.ref('pos_orders_history_reprint.group_pos_reprint', False)
        if group_reprint:
            group_reprint_name_boolean = name_boolean_group(group_reprint.id)
            group_reprint_name_selection = name_selection_groups(group_reprint.ids)
            if group_reprint_name_boolean in vals:
                vals['allow_reprint'] = vals[group_reprint_name_boolean]
                check_allow_reprint = False
            elif group_reprint_name_selection in vals:
                vals['allow_reprint'] = vals[group_reprint_name_selection]
                check_allow_reprint = False
        res = super(ResUsers, self).write(vals)
        if check_allow_reprint and 'allow_reprint' in vals:
            group_reprint = self.env.ref('pos_orders_history_reprint.group_pos_reprint', False)
            if group_reprint:
                for user in self:
                    if user.share:
                        continue
                    if vals['allow_reprint']:
                        if user not in group_reprint.users:
                            user.sudo().write({'groups_id': [(4, group_reprint.id)]})
                    else:
                        if user in group_reprint.users:
                            user.sudo().write({'groups_id': [(3, group_reprint.id)]})
        return res