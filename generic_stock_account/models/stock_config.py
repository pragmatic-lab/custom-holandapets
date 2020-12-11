from odoo import models, api, fields


class StockConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    property_cost_method = fields.Selection([
        ('standard','Precio Fijo'),
        ('average','Precio Promedio'),
        ('fifo','Primero en entrar Primero en Salir(FIFO)'),
        ], string='Metodo de coste por defecto')
    property_valuation = fields.Selection([
        ('manual_periodic', 'Periodica (manual)'),
        ('real_time', 'En tiempo real (automatizada)')
        ], string='Valoracion de inventario')
    stock_account_input_id = fields.Many2one('account.account', 
        'Cuenta de Entrada de Stock', domain=[('deprecated', '=', False)])
    stock_account_output_id = fields.Many2one('account.account', 
        'Cuenta de Salida de Stock', domain=[('deprecated', '=', False)])
    stock_account_valuation_id = fields.Many2one('account.account', 
        'Cuenta de Valoracion de Stock', domain=[('deprecated', '=', False)])

    @api.model
    def get_values(self):
        values = super(StockConfigSettings, self).get_values()
        values['property_cost_method'] = self.env['ir.property'].get('property_cost_method', 'product.category')
        values['property_valuation'] = self.env['ir.property'].get('property_valuation', 'product.category')
        # cuentas de inventario
        stock_account_input = self.env['ir.property'].get('property_stock_account_input_categ_id', 'product.category')
        if stock_account_input:
            values['stock_account_input_id'] = stock_account_input.id
        stock_account_output = self.env['ir.property'].get('property_stock_account_output_categ_id', 'product.category')
        if stock_account_output:
            values['stock_account_output_id'] = stock_account_output.id
        stock_account_valuation = self.env['ir.property'].get('property_stock_valuation_account_id', 'product.category')
        if stock_account_valuation:
            values['stock_account_valuation_id'] = stock_account_valuation.id
        return values

    @api.multi
    def set_values(self):
        super(StockConfigSettings, self).set_values()
        self.set_property_default('product.category','property_cost_method', self.property_cost_method)
        self.set_property_default('product.category','property_valuation', self.property_valuation)
        # cuentas de inventario
        self.set_property_default('product.category','property_stock_account_input_categ_id', self.stock_account_input_id.id)
        self.set_property_default('product.category','property_stock_account_output_categ_id', self.stock_account_output_id.id)
        self.set_property_default('product.category','property_stock_valuation_account_id', self.stock_account_valuation_id.id)

    @api.multi
    def set_property_default(self, model, property_name, property_value):
        property_model = self.env['ir.property']
        domain_default = property_model._get_domain(property_name, model)
        domain_default.append(('res_id', '=', False))
        property_default_value = property_model.search(domain_default, limit=1)
        if property_default_value:
            property_default_value.write({'value': property_value})
        return
    
    @api.multi
    def action_set_cost_method_products(self):
        property_model = self.env['ir.property']
        property_cost_method = self.env['ir.property'].get('property_cost_method', 'product.category')
        categ_recs = self.env['product.category'].search([])
        if categ_recs:
            values = dict.fromkeys(categ_recs.ids, property_cost_method)
            property_model.set_multi('property_cost_method', 'product.category', values)
        return True
    
    @api.multi
    def action_set_valuation_products(self):
        property_model = self.env['ir.property']
        property_valuation = self.env['ir.property'].get('property_valuation', 'product.category')
        categ_recs = self.env['product.category'].search([])
        if categ_recs:
            values = dict.fromkeys(categ_recs.ids, property_valuation)
            property_model.set_multi('property_valuation', 'product.category', values)
        return True

    @api.multi
    def action_set_account_input(self):
        property_model = self.env['ir.property']
        categ_recs = self.env['product.category'].search([])
        if categ_recs:
            values = dict.fromkeys(categ_recs.ids, self.stock_account_input_id.id)
            property_model.set_multi('property_stock_account_input_categ_id', 'product.category', values)
        return True

    @api.multi
    def action_set_account_output(self):
        self.ensure_one()
        property_model = self.env['ir.property']
        categ_recs = self.env['product.category'].search([])
        if categ_recs:
            values = dict.fromkeys(categ_recs.ids, self.stock_account_output_id.id)
            property_model.set_multi('property_stock_account_output_categ_id', 'product.category', values)
        return True
    
    @api.multi
    def action_set_account_valuation(self):
        self.ensure_one()
        property_model = self.env['ir.property']
        categ_recs = self.env['product.category'].search([])
        if categ_recs:
            values = dict.fromkeys(categ_recs.ids, self.stock_account_valuation_id.id)
            property_model.set_multi('property_stock_valuation_account_id', 'product.category', values)
        return True
