# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    Autor: Brayhan Andres Jaramillo Castaño
#    Correo: brayhanjaramillo@hotmail.com
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################

from odoo import tools
from odoo import api, fields, models


class AccountHierarchy(models.Model):
	_name = 'account.hierarchy'
	_description = "Account Hierarchy"
	_auto = False
	_order = 'code, name'

	name = fields.Char(string='Nombre', readonly=True)
	code = fields.Char(string=u'Código', readonly=True)
	move_date = fields.Date(string='Fecha', readonly=True)
	account_id = fields.Many2one(string='Cuenta', comodel_name='account.account', store=True, readonly=True)
	one_digit = fields.Char(string='1 Nivel', readonly=True)
	two_digit = fields.Char(string='2 Niveles', readonly=True)
	four_digit = fields.Char(string='4 Niveles', readonly=True)
	six_digit = fields.Char(string='6 Niveles', readonly=True)
	eight_digit = fields.Char(string='8 Niveles', readonly=True)
	company_currency_id = fields.Many2one(string='Moneda', comodel_name='res.currency', readonly=True)
	debit = fields.Monetary(string=u'Débito', default=0.0, currency_field='company_currency_id', readonly=True)
	credit = fields.Monetary(string=u'Crédito', default=0.0, currency_field='company_currency_id', readonly=True)
	balance = fields.Monetary(string='Balance', default=0.0, currency_field='company_currency_id', readonly=True)
	company_id = fields.Many2one(string=u'Compañia', comodel_name='res.company', readonly=True)
	journal_id = fields.Many2one(string='Diario', comodel_name='account.journal', readonly=True)
	user_type_id = fields.Many2one(string='Tipo', comodel_name='account.account.type', readonly=True)
	state = fields.Selection( selection=[('draft', 'Unposted'),('posted', 'Publicado')], string='Estado', default='draft', readonly=True)

	"""
	level_account = fields.Char(
		string='Nivel Cuenta',
		store=True,
		help="Nivel de la Cuenta")

	partner_id = fields.Many2one(
		string='Tercero',
		comodel_name='res.partner',
		store=True,
		readonly=True)
	user_id = fields.Many2one(
		string='Responsable',
		comodel_name='res.users',
		store=True,
		readonly=True)
	"""


	@api.model_cr
	def init(self):
		tools.drop_view_if_exists(self.env.cr, 'account_hierarchy')
		self.env.cr.execute("""
		CREATE or REPLACE VIEW account_hierarchy as (
			SELECT move_line.id as id,
				 account.code as code,
				 concat_ws(' ',account.code::text, account.name::text) as name,
				 sum(move_line.credit) as credit,
				 sum(move_line.debit) as debit,
				 sum(move_line.balance) as balance,
				 move_line.date as move_date,
				 account.id as account_id,
				-- partner.id as partner_id,
				-- user_move.id as user_id,
				 move_line.company_id as company_id,
				 move_line.company_currency_id as company_currency_id,
				 move_line.journal_id as journal_id,
				 move_line.user_type_id as user_type_id,
				 move.state as state,
				 account.one_digit as one_digit,
				 account.two_digit as two_digit,
				 account.four_digit as four_digit,
				 account.six_digit as six_digit,
				 account.eight_digit as eight_digit
				 
			FROM account_account AS account
				INNER JOIN account_move_line AS move_line
					ON (move_line.account_id=account.id)
				INNER JOIN account_move as move
					ON (move_line.move_id=move.id)
				--LEFT JOIN res_partner partner
					--ON partner.id = move_line.partner_id
				--INNER JOIN res_users user_move
					--ON user_move.id = move_line.create_uid

			GROUP BY move_line.id,
					 account.code,
					 account.name,
					 move_line.date,
					 account.id,
					 move_line.company_id,
					 move_line.journal_id,
					 move_line.user_type_id,
					 move_line.company_currency_id,
					 account.one_digit,
					 account.two_digit,
					 account.four_digit,
					 account.six_digit,
					 account.eight_digit,
					 --partner.id,
					 --user_move.id,
					 move.state
			ORDER BY account.code,
					 account.one_digit

			)""")




	@api.model
	def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
		res = super(AccountHierarchy, self).read_group(domain, fields, groupby, offset, limit=limit, orderby=orderby, lazy=lazy)
		print('*******')
		print(groupby)
		print(domain)
		return res


	"""

	SELECT code, one_digit, two_digit, four_digit, six_digit, eight_digit, 
FROM account_account					
			
CREATE OR REPLACE FUNCTION fill_account_plan_credit(val varchar) RETURNS numeric AS $$
BEGIN

RETURN (SELECT
	 sum(move_line.credit)
FROM account_account AS account
	INNER JOIN account_move_line AS move_line
		ON (move_line.account_id=account.id)
	INNER JOIN account_move as move
		ON (move_line.move_id=move.id)
WHERE account.code LIKE (val || '%'));
						 
END; $$
LANGUAGE PLPGSQL;	
	
						 
CREATE OR REPLACE FUNCTION fill_account_plan_debit(val varchar) RETURNS numeric AS $$
BEGIN

RETURN (SELECT
	 sum(move_line.debit)
FROM account_account AS account
	INNER JOIN account_move_line AS move_line
		ON (move_line.account_id=account.id)
	INNER JOIN account_move as move
		ON (move_line.move_id=move.id)
WHERE account.code LIKE (val || '%'));
						 
END; $$
LANGUAGE PLPGSQL;
						 
						 
CREATE OR REPLACE FUNCTION fill_account_plan_balance(val varchar) RETURNS numeric AS $$
BEGIN

RETURN (SELECT
	 sum(move_line.balance)
FROM account_account AS account
	INNER JOIN account_move_line AS move_line
		ON (move_line.account_id=account.id)
	INNER JOIN account_move as move
		ON (move_line.move_id=move.id)
WHERE account.code LIKE (val || '%'));
						 
END; $$
LANGUAGE PLPGSQL;	
						 
select fill_account_plan_credit('1105')	
			
			
CREATE OR REPLACE FUNCTION account_plan_update_column(val_code varchar, val_credit numeric, val_debit numeric, val_balance numeric) RETURNS VOID AS $$
BEGIN
	UPDATE account_plan_relation 
	SET credit = val_credit, debit = val_debit, balance = val_balance
	WHERE code = val_code
END; $$
LANGUAGE PLPGSQL;	
			
			
	
	CREATE OR REPLACE FUNCTION fill_initial_balance(val varchar, date_move date) RETURNS numeric AS $$
BEGIN

RETURN (SELECT
sum(move_line.balance) AS balance
FROM account_account AS account
LEFT JOIN account_move_line AS move_line
ON (move_line.account_id=account.id)
LEFT JOIN account_move as move
ON (move_line.move_id=move.id)
WHERE  move_line.date < date_move
AND move_line.account_id in (SELECT id FROM account_account WHERE code LIKE (val || '%')));					 
END; $$
LANGUAGE PLPGSQL;
		
			
			
			DROP TABLE IF EXISTS account_plan_relation;
			SELECT
				 account.code as code,
				 concat_ws(' ',account.code::text, account.name::text) as name,
				 sum(move_line.credit) as credit,
				 sum(move_line.debit) as debit,
				 sum(move_line.balance) as balance,
				 move_line.date as move_date,
				 account.id as account_id,
				-- partner.id as partner_id,
				-- user_move.id as user_id,
				 move_line.company_id as company_id,
				 move_line.company_currency_id as company_currency_id,
				 move_line.journal_id as journal_id,
				 move_line.user_type_id as user_type_id,
				 move.state as state
			INTO account_plan_relation
			FROM account_account AS account
				LEFT JOIN account_move_line AS move_line
					ON (move_line.account_id=account.id)
				LEFT JOIN account_move as move
					ON (move_line.move_id=move.id)
				--LEFT JOIN res_partner partner
					--ON partner.id = move_line.partner_id
				--INNER JOIN res_users user_move
					--ON user_move.id = move_line.create_uid

			GROUP BY 
					 account.code,
					 account.name,
					 move_line.date,
					 account.id,
					 move_line.company_id,
					 move_line.journal_id,
					 move_line.user_type_id,
					 move_line.company_currency_id,
					 --partner.id,
					 --user_move.id,
					 move.state
			ORDER BY account.code;
			SELECT * FROM account_plan_relation;
						 

	"""
		
AccountHierarchy()