from odoo import models, api, fields
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round


class Uom(models.Model):

    _inherit = ['translations.unique', 'mail.thread', 'uom.uom']
    _name = 'uom.uom'
    _check_translations = True
    
    @api.depends('uom_type','category_id')
    def _compute_uom_reference(self):
        uom_reference = self.browse()
        for uom in self:
            uom_reference = self.browse()
            if uom.category_id:
                uom_reference = self.search([
                    ('category_id','=', uom.category_id.id),
                    ('uom_type','=', 'reference'),
                ], limit=1)
            uom.uom_reference_id = uom_reference
        
    @api.depends('uom_type','category_id', 'uom_reference_id', 'factor', 'factor_inv', 'rounding')
    def _compute_value_uom(self):
        for uom in self:
            value_uom = 0
            qty = 1
            if uom.uom_reference_id and uom.factor_inv != 0:
                value_uom = qty / (1/uom.factor_inv)
                value_uom = value_uom * uom.uom_reference_id.factor
                value_uom = float_round(value_uom, precision_rounding=uom.rounding)
            uom.value_uom = value_uom
    
    uom_reference_id = fields.Many2one('uom.uom', u'Unidad de Medida de referencia', 
        compute="_compute_uom_reference")
    value_uom = fields.Float(u'Valor en UdM de referencia', digits=(16, 6),
        compute="_compute_value_uom")
    #reemplazar campos para que se agregue log en mensajeria cuando cambien valores
    category_id = fields.Many2one('uom.category', track_visibility='onchange')
    factor = fields.Float(track_visibility='onchange')
    uom_type = fields.Selection(track_visibility='onchange')
    
    @api.onchange('uom_type')
    def _onchange_uom_type(self):
        res = super(Uom, self)._onchange_uom_type()
        if self.uom_type == 'reference':
            self.rounding = 1
        else:
            self.rounding = 0.00001
        return res
