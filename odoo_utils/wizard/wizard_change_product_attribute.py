from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class WizardChangeProductAttribute(models.TransientModel):
    _name = 'wizard.change.product.attribute'
    _description = u'wizard.change.product.attribute'
    
    attribute_id = fields.Many2one('product.attribute', 'Atributo Actual')
    new_attribute_id = fields.Many2one('product.attribute', 'Nuevo Atributo')
    line_ids = fields.One2many('wizard.change.product.attribute.line', 'wizard_id', u'Atributos a cambiar')
    product_id = fields.Many2one('product.template', u'Producto')
    attribute_ids = fields.Many2many('product.attribute', 'wizard_change_product_attribute_product_attribute_rel', 'wizard_id', 'attribute_id', u'Attributos')
    
    @api.model
    def default_get(self, fields_list):
        values = super(WizardChangeProductAttribute, self).default_get(fields_list)
        product_ids = self.env.context.get('active_ids')
        if len(product_ids) != 1:
            raise UserError(_(u"Solo puede utilizaar este asistente en 1 producto a la vez"))
        if product_ids:
            product = self.env['product.template'].browse(product_ids[0])
            values['product_id'] = product.id
            values['attribute_ids'] = [(6, 0, product.attribute_line_ids.mapped('attribute_id').ids)]
        return values
    
    @api.onchange('attribute_id',)
    def onchange_attribute(self):
        line_ids = [(5, 0)]
        for attribute in self.product_id.attribute_line_ids:
            if attribute.attribute_id == self.attribute_id:
                for value in attribute.value_ids:
                    line_ids.append({
                        'attribute_value_id': value.id,
                    })
        self.line_ids = line_ids
        
    @api.onchange('new_attribute_id',)
    def onchange_new_attribute(self):
        for line in self.line_ids:
            line.new_attribute_value_id = False
    
    @api.multi
    def action_process(self):
        if self.line_ids.filtered(lambda x: not x.new_attribute_value_id):
            raise UserError("Por favor seleccione el nuevo valor en cada linea")
        all_values_to_remove = []
        for attribute in self.product_id.attribute_line_ids:
            if attribute.attribute_id == self.attribute_id:
                all_values_to_remove.extend(attribute.value_ids.ids)
                attribute.write({
                    'attribute_id': self.new_attribute_id.id,
                    'value_ids': [(6, 0, self.line_ids.mapped('new_attribute_value_id').ids)],
                })
        for variant in self.product_id.product_variant_ids:
            for value in variant.attribute_value_ids:
                for new_value in self.line_ids:
                    if value == new_value.attribute_value_id:
                        variant.write({
                            'attribute_value_ids': [(4, new_value.new_attribute_value_id.id), (3, value.id)]
                        })
        if all_values_to_remove:
            template_values = self.env['product.template.attribute.value'].search([
                ('product_tmpl_id', '=', self.product_id.id),
                ('product_attribute_value_id', 'in', all_values_to_remove)]
            )
            template_values.unlink()
        return {'type': 'ir.actions.act_window_close'}


class WizardChangeProductAttributeLine(models.TransientModel):
    _name = 'wizard.change.product.attribute.line'
    _description = u'wizard.change.product.attribute.line'
    
    wizard_id = fields.Many2one('wizard.change.product.attribute', u'Parent')
    attribute_value_id = fields.Many2one('product.attribute.value', 'Valor actual')
    new_attribute_value_id = fields.Many2one('product.attribute.value', 'Nuevo Valor')
