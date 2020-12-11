from odoo import models, api, fields
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo import tools


class ReportPosPayment(models.Model):    
    _name = 'report.pos.payment'
    _description = 'Analisis de pagos del TPV'
    _auto = False
    _rec_name = 'journal_id' 
    
    amount_total = fields.Float('Saldo Final', digits=dp.get_precision('Account'), readonly=True)
    date = fields.Date('Fecha', readonly=True)
    create_uid = fields.Many2one('res.users', 'Responsable', readonly=True)
    company_id = fields.Many2one('res.company', 'Compañia', readonly=True)
    journal_id = fields.Many2one('account.journal', 'Diario', readonly=True)
    config_id = fields.Many2one('pos.config', 'Punto de venta', readonly=True)
    session_id = fields.Many2one('pos.session', 'Sesion', readonly=True)
    order_id = fields.Many2one('pos.order', 'Pedido/Factura', readonly=True)
    payment_term_id = fields.Many2one('account.payment.term', 'Plazos de Pago', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Cliente', readonly=True)
    commercial_partner_id = fields.Many2one('res.partner', string='Empresa', readonly=True)
    commercial_parent_id = fields.Many2one('res.partner', string='Contacto Principal', readonly=True)
    journal_type = fields.Selection([
        ('cash', 'Efectivo'), 
        ('bank', 'Bancos y cheques'), 
        ], string='Tipo de pago', readonly=True)
    state = fields.Selection([
        ('draft', 'Nuevo'),
        ('open','Abierto'),
        ('confirm', 'Cerrado')
        ], string='Estado', readonly=True)
    
    def _select(self):
        return """
            SELECT
                l.id AS id,
                SUM(l.amount)AS amount_total,
                l.date AS date,
                l.create_uid AS create_uid,
                l.company_id AS company_id,
                j.id AS journal_id, 
                j.type AS journal_type,
                s.config_id AS config_id,
                s.id AS session_id,
                l.pos_statement_id AS order_id,
                po.partner_id,
                po.commercial_partner_id,
                po.commercial_parent_id,
                po.payment_term_id,
                b.state
        """
        
    def _from(self):
        return """
            FROM account_bank_statement_line l
                INNER JOIN account_bank_statement b ON b.id = l.statement_id
                INNER JOIN account_journal j ON j.id = b.journal_id
                INNER JOIN pos_session s ON s.id = b.pos_session_id
                INNER JOIN pos_config c ON c.id = s.config_id
                LEFT JOIN pos_order po ON po.id = l.pos_statement_id
        """
        
    def _where(self):
        return """
            WHERE j.type IN ('cash', 'bank')
        """
        
    def _group_by(self):
        return """
            GROUP BY l.id, j.id, b.state, s.id, s.config_id, l.pos_statement_id,
                po.partner_id, po.commercial_partner_id, po.commercial_parent_id, po.payment_term_id
        """

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
                %s
                %s
                %s
            )
        """ % (self._table, self._select(), self._from(), self._where(), self._group_by())
        )
