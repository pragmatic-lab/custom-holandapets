from odoo import models, api, fields


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=80):
        if not args:
            args=[]
        recs = self.browse()
        res = super(StockProductionLot, self).name_search(name, args, operator, limit)
        #buscar por el campo ref
        if name and not res:
            recs = self.search([('ref','ilike',name)] + args, limit=limit)
            res = recs.name_get()
        return res
    
    @api.multi
    def name_get(self):
        res = []
        for lot in self:
            name = lot.name
            if lot.ref:
                name = "%s (%s)" % (name, lot.ref)
            res.append((lot.id, name))
        return res
