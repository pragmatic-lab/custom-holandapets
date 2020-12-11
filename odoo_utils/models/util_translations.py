from odoo import models, api, fields
from odoo.exceptions import UserError, ValidationError


class UtilTranslations(models.AbstractModel):
    _name = 'translations.unique'
    _description = 'Traduccion Unica'
    _check_translations = False
    _fields_check = []

    @api.multi
    def _check_field_duplicity_translation(self, field_name, new_name): 
        #FIX: no es una restriccion, xq a pesar de lanzar la excepcion, no me revertia los cambios en el write
        SQL = """SELECT value 
                FROM ir_translation
                WHERE name = %(res_name)s
                    AND (src ilike %(new_name)s OR value ilike %(new_name)s)
                    AND res_id != %(res_id)s 
        """
        res_name = "%s,%s" % (self._name, field_name)
        field_string = self._fields[field_name].string
        for res_id in self.ids:
            self.env.cr.execute(SQL, {'res_name': res_name,'new_name': new_name, 'res_id': res_id})
            if self.env.cr.fetchone():
                raise UserError("Ya existe otro registro con el campo %s = %s, "\
                                "por favor verifique en todos los idiomas de ser necesario." % (field_string, new_name))
            else:
                SQL = """SELECT id 
                            FROM %s
                            WHERE %s ilike %s AND id != %s
                    """ % (self._table, field_name, '%(new_name)s', '%(res_id)s')
                self.env.cr.execute(SQL, {'new_name': new_name, 'res_id': res_id})
                if self.env.cr.fetchone():
                    raise UserError("Ya existe otro registro con el campo %s = %s, "\
                                "por favor verifique en todos los idiomas de ser necesario." % (field_string, new_name))
        return True
    
    @api.multi
    def write(self, vals):
        if self._check_translations:
            if not self._fields_check and 'name' in self._fields:
                self._fields_check.append('name')
            for field_name in self._fields_check:
                if field_name in vals and vals.get(field_name, ''):
                    self._check_field_duplicity_translation(field_name, vals[field_name])
        res = super(UtilTranslations, self).write(vals)
        return res
    
    @api.model
    def create(self, vals):
        new_rec = super(UtilTranslations, self).create(vals)
        if self._check_translations:
            if not self._fields_check and 'name' in self._fields:
                self._fields_check.append('name')
            for field_name in self._fields_check:
                if field_name in vals and vals.get(field_name, ''):
                    new_rec._check_field_duplicity_translation(field_name, vals[field_name])
        return new_rec
