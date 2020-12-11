	def query_insert_model(self):
		"""
			Funcion que permite realizar la creacion de los registros
		"""
		#data = self.return_data_model()
		self.query_delete_model()

		sql = """
			INSERT INTO account_partner_report_move_view 
			(partner_id, 
			 l10n_co_document_type, 
			 vat, 
			 first_name, 
			 second_name, 
			 first_surname, 
			 second_surname, 
			 name, 
			 street, 
			 street2, 
			 state_id, 
			 country_id, 
			 account_id, 
			 credit, 
			 debit, 
			 balance,
			 account_move_id,
			 account_ml_id,
			 date)
			(
			SELECT
				aml.partner_id AS partner_id,
				partner.l10n_co_document_type AS l10n_co_document_type,
				partner.vat AS vat,
				partner.first_surname AS first_name,
				partner.second_name AS second_name,	
				partner.first_surname AS first_surname,
				partner.second_surname AS second_surname,
				partner.name AS name,
				partner.street AS street,
				partner.street2 AS street2,	
				rcs.id as state_id,
				rc.id AS country_id,
				aml.account_id AS account_id,
				aml.credit AS credit,
				aml.debit AS debit,
				aml.balance AS balance,
				aml.move_id,
				aml.id,
				aml.date
				
			FROM  account_move_line aml
				INNER JOIN account_account AS account
				ON (aml.account_id = account.id)
				
				INNER JOIN res_partner AS partner
				ON (aml.partner_id = partner.id)
				
				LEFT JOIN res_country AS rc
				ON (partner.country_id = rc.id)
				
				LEFT JOIN res_country_state AS rcs
				ON (partner.state_id = rcs.id)
			

			"""

		sql += " WHERE aml.company_id = '" + str(self.env.user.company_id.id) + "' AND aml.date BETWEEN '" + str(self.date_from) + "' AND '" + str(self.date_to) + "' "
		#sql = sql + " WHERE aml.date BETWEEN '" + str(self.date_from) + "' AND '" + str(self.date_to) + "' "
		if self.partner_ids:
			partner_ids = ''
			for x in self.partner_ids:
				partner_ids += str(x.id) + "," 
			sql += "\n AND aml.partner_id IN (" + partner_ids[:len(partner_ids)-1] + ") "

		if self.account_ids:
			account_ids = ''
			for x in self.account_ids:
				account_ids += str(x.id) + "," 
			sql += "\n AND aml.account_id IN (" + account_ids[:len(account_ids)-1] + ") "

		sql += ')'
		self.env.cr.execute(sql)
