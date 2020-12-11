from odoo import fields, models, api

from odoo.addons.base.models.res_users import name_boolean_group, name_selection_groups

class ResUsers(models.Model):
    _inherit = 'res.users'

    allow_credit_note = fields.Boolean('Allow Credit Notes', default=True)
    
    @api.model
    def create(self, vals):
        new_rec = super(ResUsers, self).create(vals)
        for user in new_rec:
            if user.share:
                continue
            group_credit_note = self.env.ref('pos_orders_history_return.group_generate_credit_note', False)
            if user.allow_credit_note:
                if user not in group_credit_note.users:
                    user.sudo().write({'groups_id': [(4, group_credit_note.id)]})
            else:
                if user in group_credit_note.users:
                    user.sudo().write({'groups_id': [(3, group_credit_note.id)]})
        return new_rec
    
    @api.multi
    def write(self, vals):
        check_allow_credit_note = True
        group_credit_note = self.env.ref('pos_orders_history_return.group_generate_credit_note', False)
        if group_credit_note:
            group_credit_note_name_boolean = name_boolean_group(group_credit_note.id)
            group_credit_note_name_selection = name_selection_groups(group_credit_note.ids)
            if group_credit_note_name_boolean in vals:
                vals['allow_credit_note'] = vals[group_credit_note_name_boolean]
                check_allow_credit_note = False
            elif group_credit_note_name_selection in vals:
                vals['allow_credit_note'] = vals[group_credit_note_name_selection]
                check_allow_credit_note = False
        res = super(ResUsers, self).write(vals)
        if check_allow_credit_note and 'allow_credit_note' in vals:
            group_credit_note = self.env.ref('pos_orders_history_return.group_generate_credit_note', False)
            if group_credit_note:
                for user in self:
                    if user.share:
                        continue
                    if vals['allow_credit_note']:
                        if user not in group_credit_note.users:
                            user.sudo().write({'groups_id': [(4, group_credit_note.id)]})
                    else:
                        if user in group_credit_note.users:
                            user.sudo().write({'groups_id': [(3, group_credit_note.id)]})
        return res