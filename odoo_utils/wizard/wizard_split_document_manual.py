from odoo import models, api, fields


class WizardSplitDocumentManual(models.TransientModel):
    _name = 'wizard.split.document.manual'
    _description = 'Asistente para dividir documentos creados manualmente'
    
    model_name = fields.Char('Nombre de Modelo')
    document_number = fields.Integer('Documentos resultantes', readonly=True)
    document_lines = fields.Integer('Numero máximo de lineas por documento', readonly=True)

    @api.multi
    def show_view(self, name='Dividir Documentos', 
                  view_idxml='odoo_utils.wizard_split_document_manual_form_view', 
                  view_mode='tree,form', 
                  nodestroy=True, 
                  target='new'):
        return self.env['odoo.utils'].show_view(name, self._name, view_idxml, self.id, view_mode=view_mode, nodestroy=nodestroy, target=target)
    
    @api.multi
    def _action_split_document(self, active_model, active_ids):
        return {'type': 'ir.actions.act_window_close'}
    
    @api.multi
    def action_process(self):
        active_ids = self.env.context.get('active_ids',[])
        result = self._action_split_document(self.model_name, active_ids)
        return result
