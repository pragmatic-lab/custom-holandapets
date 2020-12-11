from odoo import models, api, fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.multi
    def name_get(self):
        result = []
        for aml in self:
            name = aml.name if aml.name != aml.move_id.name else aml.move_id.name
            if aml.ref:
                name = '%(name)s (%(ref)s)' % {'name': name, 'ref': aml.ref}
            #si tiene factura, tomar la referencia, esta tiene el nombre correcto
            if aml.invoice_id:
                name = aml.ref
            result.append((aml.id, name))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=80):
        if not args:
            args = []
        invoice_model = self.env['account.invoice']
        aml_recs = self.browse()
        if name:
            aml_recs = self.search([('ref', operator, name)] + args, limit=limit)
            if not aml_recs:
                aml_recs = self.search([('name', operator, name)] + args, limit=limit)
            if not aml_recs:
                aml_recs = self.search([('move_id.name', operator, name)] + args, limit=limit)
            move_ids = []
            if not aml_recs:
                invoice_ids = [x[0] for x in invoice_model.name_search(name, args=[], operator=operator, limit=limit)]
                move_ids = invoice_model.browse(invoice_ids).mapped('move_id').ids
            if move_ids:
                args += [('move_id','in', move_ids)]
                aml_recs = self.search(args, limit=limit)
        else:
            aml_recs = self.search(args, limit=limit)
        return aml_recs.name_get()
