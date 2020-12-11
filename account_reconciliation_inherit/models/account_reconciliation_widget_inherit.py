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

import calendar
import json 
import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta
from odoo import api, models, fields, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import AccessError, UserError
from odoo.tools.misc import formatLang
from odoo.tools import misc
import logging
_logger = logging.getLogger(__name__)

class AccountReconciliationInherit(models.AbstractModel):
	_inherit = 'account.reconciliation.widget'


	def validate_date_records_reconcile(self, date):


		account_bs_id = self._context.get('account_bs')

		if account_bs_id:	

			account_bs_line_ids = self.env['account.bank.statement.line'].search([('statement_id', '=', account_bs_id)])
			
			_logger.info(account_bs_line_ids)
			dates = []

			if account_bs_line_ids:
				for x in account_bs_line_ids:
					dates.append(x.date)

			dates.sort()
			
			date_begin = dates[0]
			date_end = dates[len(dates)-1]

			if str(line['date'])[5:7] == str(date_end)[5:7] and str(line['date_maturity'])[5:7] == str(date_end)[5:7]:
				pass

		return results


	def validate_date_records(self, results):
		"""
			Funcion que permite validar que los resultados que muestren sean de acuerdo a las fechas configuradas en 
			el extrato bancario
		"""
	
		account_bs_id = self._context.get('account_bs')
		_logger.info('**********************************')
		_logger.info(account_bs_id)
		_logger.info(self.env.context)
		if account_bs_id:	

			account_bs_line_ids = self.env['account.bank.statement.line'].search([('statement_id', '=', account_bs_id)])
			
			_logger.info(account_bs_line_ids)
			dates = []

			if account_bs_line_ids:
				for x in account_bs_line_ids:
					dates.append(x.date)

			dates.sort()
			
			date_begin = dates[0]
			date_end = dates[len(dates)-1]

			if results:
				for x in results.get('lines'):

					if len(x.get('reconciliation_proposition') ) > 0:						
						flag = 0
						new_val = []
						for line in x.get('reconciliation_proposition'):
							#if line['already_paid'] == False:
							#print(line['date'])
							if str(line['date'])[5:7] == str(date_end)[5:7] and str(line['date_maturity'])[5:7] == str(date_end)[5:7]:
								new_val.append(line)
						x['reconciliation_proposition'] = new_val

		return results


	# def validate_date_recordss(self, results):
	# 	"""
	# 		Funcion que permite validar que los resultados que muestren sean de acuerdo a las fechas configuradas en 
	# 		el extrato bancario
	# 	"""
	# 	_logger.info('Entrando en la eliminacion de las fechas')
	# 	account_bs_id = self._context.get('account_bs')
	# 	if account_bs_id:	

	# 		account_bs_line_ids = self.env['account.bank.statement.line'].search([('statement_id', '=', account_bs_id)])
			
	# 		dates = []

	# 		if account_bs_line_ids:
	# 			for x in account_bs_line_ids:
	# 				dates.append(x.date)

	# 		dates.sort()
			
	# 		date_begin = dates[0]
	# 		date_end = dates[len(dates)-1]

	# 		if results:
	# 			for x in results.get('lines'):

	# 				if len(x.get('reconciliation_proposition') ) > 0:						
	# 					flag = 0
	# 					new_val = []
	# 					for line in x.get('reconciliation_proposition'):
	# 						#if line['already_paid'] == False:
	# 						print(line['date'])
	# 						if str(line['date'])[5:7] == str(date_end)[5:7] and str(line['date_maturity'])[5:7] == str(date_end)[5:7]:
	# 							new_val.append(line)
	# 					x['reconciliation_proposition'] = new_val

	# 	return results


	def validate_show_records(self, results):
		"""
			Funcion que permite ocultar registros que no esten pagos
		"""
		hide_record = self._context.get('hide_record')

		if hide_record:		

			for x in range(2):
				for x in results.get('lines'):

					flag = 0
					for line in x.get('reconciliation_proposition'):
						if line.get('already_paid') == False:
							x.get('reconciliation_proposition').pop(flag)
						flag +=1
		return results


	@api.model
	def get_bank_statement_data(self, bank_statement_ids):
		""" Get statement lines of the specified statements or all unreconciled
			statement lines and try to automatically reconcile them / find them
			a partner.
			Return ids of statement lines left to reconcile and other data for
			the reconciliation widget.

			:param st_line_id: ids of the bank statement
		"""

		_logger.info('#################')

		#
		_logger.info(self)

		bank_statements = self.env['account.bank.statement'].browse(bank_statement_ids)

		query = '''
			 SELECT line.id
			 FROM account_bank_statement_line line
			 WHERE account_id IS NULL
			 AND line.amount != 0.0
			 AND line.statement_id IN %s
			 AND NOT EXISTS (SELECT 1 from account_move_line aml WHERE aml.statement_line_id = line.id)
		'''
		self.env.cr.execute(query, [tuple(bank_statements.ids)])

		bank_statement_lines = self.env['account.bank.statement.line'].browse([line.get('id') for line in self.env.cr.dictfetchall()])

		results =self.get_bank_statement_line_data(bank_statement_lines.ids)
		
		bank_statement_lines_left = self.env['account.bank.statement.line'].browse([line['st_line']['id'] for line in results['lines']])
		bank_statements_left = bank_statement_lines_left.mapped('statement_id')

		results.update({
			'statement_name': len(bank_statements_left) == 1 and bank_statements_left.name or False,
			'journal_id': bank_statements and bank_statements[0].journal_id.id or False,
			'notifications': []
		})

		if len(results['lines']) < len(bank_statement_lines):
			results['notifications'].append({
				'type': 'info',
				'template': 'reconciliation.notification.reconciled',
				'reconciled_aml_ids': results['reconciled_aml_ids'],
				'nb_reconciled_lines': results['value_min'],
				'details': {
					'name': _('Journal Items'),
					'model': 'account.move.line',
					'ids': results['reconciled_aml_ids'],
				}
			})

		#print(results)
		#self.validate_show_records(results)
		#self.validate_date_records(results)
		#_logger.info(results)
		#print('El resultado es:')
		#print(results)
		return results

	@api.model
	def _prepare_move_lines(self, move_lines, target_currency=False, target_date=False, recs_count=0):
		""" Returns move lines formatted for the manual/bank reconciliation widget

			:param move_line_ids:
			:param target_currency: currency (browse) you want the move line debit/credit converted into
			:param target_date: date to use for the monetary conversion
		"""
		#print('hjgjhfjf por aca es:')
		#print(self)
		#print(self.env.context)
		context = dict(self._context or {})
		#print(context)
		ret = []
		ret_line = {}
		flag = False

		date_record = None

		if self._context.get('date_to_validate') and self._context.get('hide_record'):
			account_bs_id = self._context.get('account_bs')

			if account_bs_id:	

				account_bs_line_ids = self.env['account.bank.statement'].search([('id', '=', account_bs_id)])
				#print(account_bs_line_ids.date)
				date_record = account_bs_line_ids.date


		for line in move_lines:
			company_currency = line.company_id.currency_id
			line_currency = (line.currency_id and line.amount_currency) and line.currency_id or company_currency
			date_maturity = misc.format_date(self.env, line.date_maturity, lang_code=self.env.user.lang)

			if self._context.get('hide_record'):
				print('sisas')
				date_record_month = str(date_record)[5:7]
				print(date_record_month + ' ' + str(line.date)[5:7])
				if date_record_month == str(line.date)[5:7]:
					flag = True

					print(line.date)
					ret_line = {
						'id': line.id,
						'name': line.name and line.name != '/' and line.move_id.name + ': ' + line.name or line.move_id.name,
						'ref': line.move_id.ref or '',
						# For reconciliation between statement transactions and already registered payments (eg. checks)
						# NB : we don't use the 'reconciled' field because the line we're selecting is not the one that gets reconciled
						'account_id': [line.account_id.id, line.account_id.display_name],
						'already_paid': line.account_id.internal_type == 'liquidity',
						'account_code': line.account_id.code,
						'account_name': line.account_id.name,
						'account_type': line.account_id.internal_type,
						'date_maturity': date_maturity,
						'date': line.date,
						'journal_id': [line.journal_id.id, line.journal_id.display_name],
						'partner_id': line.partner_id.id,
						'partner_name': line.partner_id.name,
						'currency_id': line_currency.id,
					}
			else:
				flag = True
				ret_line = {
				'id': line.id,
				'name': line.name and line.name != '/' and line.move_id.name + ': ' + line.name or line.move_id.name,
				'ref': line.move_id.ref or '',
				# For reconciliation between statement transactions and already registered payments (eg. checks)
				# NB : we don't use the 'reconciled' field because the line we're selecting is not the one that gets reconciled
				'account_id': [line.account_id.id, line.account_id.display_name],
				'already_paid': line.account_id.internal_type == 'liquidity',
				'account_code': line.account_id.code,
				'account_name': line.account_id.name,
				'account_type': line.account_id.internal_type,
				'date_maturity': date_maturity,
				'date': line.date,
				'journal_id': [line.journal_id.id, line.journal_id.display_name],
				'partner_id': line.partner_id.id,
				'partner_name': line.partner_id.name,
				'currency_id': line_currency.id,
			}

			debit = line.debit
			credit = line.credit
			amount = line.amount_residual
			amount_currency = line.amount_residual_currency

			# For already reconciled lines, don't use amount_residual(_currency)
			if line.account_id.internal_type == 'liquidity':
				amount = debit - credit
				amount_currency = line.amount_currency

			target_currency = target_currency or company_currency

			# Use case:
			# Let's assume that company currency is in USD and that we have the 3 following move lines
			#      Debit  Credit  Amount currency  Currency
			# 1)    25      0            0            NULL
			# 2)    17      0           25             EUR
			# 3)    33      0           25             YEN
			#
			# If we ask to see the information in the reconciliation widget in company currency, we want to see
			# The following information
			# 1) 25 USD (no currency information)
			# 2) 17 USD [25 EUR] (show 25 euro in currency information, in the little bill)
			# 3) 33 USD [25 YEN] (show 25 yen in currency information)
			#
			# If we ask to see the information in another currency than the company let's say EUR
			# 1) 35 EUR [25 USD]
			# 2) 25 EUR (no currency information)
			# 3) 50 EUR [25 YEN]
			# In that case, we have to convert the debit-credit to the currency we want and we show next to it
			# the value of the amount_currency or the debit-credit if no amount currency
			if target_currency == company_currency:
				if line_currency == target_currency:
					amount = amount
					amount_currency = ""
					total_amount = debit - credit
					total_amount_currency = ""
				else:
					amount = amount
					amount_currency = amount_currency
					total_amount = debit - credit
					total_amount_currency = line.amount_currency

			if target_currency != company_currency:
				if line_currency == target_currency:
					amount = amount_currency
					amount_currency = ""
					total_amount = line.amount_currency
					total_amount_currency = ""
				else:
					amount_currency = line.currency_id and amount_currency or amount
					company = line.account_id.company_id
					date = target_date or line.date
					amount = company_currency._convert(amount, target_currency, company, date)
					total_amount = company_currency._convert((line.debit - line.credit), target_currency, company, date)
					total_amount_currency = line.currency_id and line.amount_currency or (line.debit - line.credit)

			if flag:
				ret_line['recs_count'] = recs_count
				ret_line['debit'] = amount > 0 and amount or 0
				ret_line['credit'] = amount < 0 and -amount or 0
				ret_line['amount_currency'] = amount_currency
				ret_line['amount_str'] = formatLang(self.env, abs(amount), currency_obj=target_currency)
				ret_line['total_amount_str'] = formatLang(self.env, abs(total_amount), currency_obj=target_currency)
				ret_line['amount_currency_str'] = amount_currency and formatLang(self.env, abs(amount_currency), currency_obj=line_currency) or ""
				ret_line['total_amount_currency_str'] = total_amount_currency and formatLang(self.env, abs(total_amount_currency), currency_obj=line_currency) or ""
				ret.append(ret_line)
		return ret



AccountReconciliationInherit()