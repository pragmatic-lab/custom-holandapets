import logging

from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class WizardCorrectRecord(models.TransientModel):
    _name = 'wizard.correct.record'
    _description = 'wizard.correct.record'
    
    @api.model
    def _get_options(self):
        return [('journal', 'Diarios Contables')]
    
    journal_dest_id = fields.Many2one('account.journal', 'Nuevo Diario', required=False, help="",)
    journal_origin_ids = fields.Many2many('account.journal', 'wizard_correct_record_journal_rel', 
        'wizard_id', 'journal_id', 'Diarios a reemplazar', help="",)
    delete_record = fields.Boolean('Eliminar Registro al finalizar?', readonly=False, help="",)
    record_option = fields.Selection('_get_options', string='Registros a modificar', help="",)
    
    @api.multi
    def _action_change_records(self, record_origin, record_dest, objects_skip=None):
        if objects_skip is None:
            objects_skip = []
        cr = self.env.cr
        domain = [
            ('ttype','in',('many2one', 'many2many')),
            ('relation','=',record_origin._name),
            ('store','=',True),
            ]
        if objects_skip:
            domain.append(('model_id.model', 'not in', objects_skip))
        fields_to_change = self.env['ir.model.fields'].search(domain)
        #modificaciones hacerlas por BD para no hacer lento el proceso con disparadores de campos funcionales
        #campos m2o modificar directamente en la tabla, TODO: si el campo es de otra tabla(via herencia por delegacion)
        #campos m2m modificar en la tabla relacionada
        updates = []
        query = ""
        params = False
        record_origin_name = record_origin.display_name
        record_dest_name = record_dest.display_name
        for field in fields_to_change:
            updates = []
            res_model = self.env[field.model_id.model].with_context(active_test=False) #buscar registros inactivos tambien
            if res_model._name == self._name:
                continue
            if not res_model._auto:
                _logger.info("Saltando modelo: %s con el campo: %s, es una vista de analisis", res_model._name, field.name)
                continue
            domain = []
            domain.append((field.name, '=', record_origin.id))
            domain.append((field.name, '!=', record_dest.id))
            records_update = res_model.search(domain)
            if not records_update:
                _logger.info("No hay registros en modelo: %s para el campo: %s %s", res_model._name, field.name, record_origin_name)
                continue
            _logger.info("Modificando %s registros en modelo: %s para el campo: %s. Antiguo valor: %s, Nuevo Valor: %s", 
                         len(records_update), res_model._name, field.name, record_origin_name, record_dest_name)
            if field.ttype == 'many2one':
                updates.append((field.name, '%s', record_dest.id))
                query = 'UPDATE "%s" SET %s WHERE id IN %%s' % (
                    res_model._table, ','.join('"%s"=%s' % (u[0], u[1]) for u in updates),
                )
                params = tuple(u[2] for u in updates if len(u) > 2)
                for sub_ids in cr.split_for_in_conditions(set(records_update.ids)):
                    cr.execute(query, params + (sub_ids,))
            elif field.ttype == 'many2many':
                for record in records_update:
                    record.write({field.name: [(3, record_origin.id)]})
                    record.write({field.name: [(4, record_dest.id)]})
        return True
    
    @api.multi
    def action_process(self):
        if self.record_option == 'journal':
            account_delete = self.env['account.account'].browse()
            journal_delete = self.env['account.journal'].browse()
            journal_dest = self.journal_dest_id.with_context(show_full_name=True)
            for journal_origin in self.journal_origin_ids.with_context(show_full_name=True):
                if journal_origin == journal_dest:
                    raise UserError("Los diarios no pueden ser los mismos, por favor seleccione diarios diferentes")
                if journal_origin.default_credit_account_id and journal_dest.default_credit_account_id:
                    self._action_change_records(journal_origin.default_credit_account_id, journal_dest.default_credit_account_id)
                if journal_origin.default_debit_account_id and journal_dest.default_debit_account_id:
                    self._action_change_records(journal_origin.default_debit_account_id, journal_dest.default_debit_account_id)
                self._action_change_records(journal_origin, journal_dest)
                if self.delete_record:
                    if journal_origin.default_credit_account_id:
                        account_delete |= journal_origin.default_credit_account_id
                    if journal_origin.default_debit_account_id:
                        account_delete |= journal_origin.default_debit_account_id
                    journal_delete |= journal_origin
            if account_delete:
                account_delete.unlink()
            if journal_delete:
                journal_delete.unlink()
        return True
