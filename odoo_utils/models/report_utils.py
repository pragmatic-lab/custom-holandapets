import logging

from odoo import models, api, fields, tools

_logger = logging.getLogger(__name__)


class ReportUtils(models.AbstractModel):
    _name = 'report.utils'
    _description = 'Utilidades para reportes'
        
    LETTERS = list(map(chr, list(range(65, 91))))
    
    @api.model
    def GetLetterForPosition(self, position):
        '''
        cuando hay muchas columnas(A-Z)
        se empieza con AA, AB, AC, AD, A....
        y asi en adelante BA, BB, BC, BD, B...
        asi que controlar eso
        por cada vez que se completa un rango, iniciar con el siguiente segun el abecedario
        '''
        letter = ""
        if position > 25:
            multiplicador, remaing = divmod(position, 25)
            if multiplicador > 0:
                remaing -= multiplicador
                multiplicador -= 1
            letter = "%s%s" % (self.LETTERS[multiplicador], self.LETTERS[remaing])
        else:
            letter = self.LETTERS[position]
        return letter
