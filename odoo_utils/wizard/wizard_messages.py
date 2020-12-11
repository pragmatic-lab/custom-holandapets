from odoo import models, fields, api

class WizardMessages(models.TransientModel):
    '''
    Utilidad para Presentar Mensajes
    '''
    _name = 'wizard.messages'
    _description = 'Utilidad para Presentar Mensajes'

    message = fields.Html('Mensaje', readonly=True)
