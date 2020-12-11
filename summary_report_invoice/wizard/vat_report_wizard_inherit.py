# Copyright  2018 Forest and Biomass Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval
from odoo.tools import pycompat
from odoo.exceptions import ValidationError


class VATReportWizardInherit(models.TransientModel):
	_inherit = "vat.report.wizard"
	_description = "VAT Report Wizard"


	date_from = fields.Datetime('Start Date', required=True)
	date_to = fields.Datetime('End Date', required=True)

	def prepare_vat_report(self, company_id, date_from, date_to):

		print('preparando el reporte')
		print(date_from)
	
		return {
			'company_id': company_id,
			'date_from': date_from,
			'date_to': date_to,
			'based_on': 'taxgroups',
			'tax_detail': True,
		}
		
	def export(self, report_type, company_id, date_from, date_to, validate, user_id):

		print('la fecha que esta llegand es:')
		print(date_from)
		model = self.env['report_vat_report']
		report = model.create(self.prepare_vat_report(company_id, date_from, date_to))
		if validate == 1:
			report.compute_data_for_report_(user_id)
		else:
			report.compute_data_for_report()
		return report.print_report(report_type)

VATReportWizardInherit()
	
class VATReportInherit(models.TransientModel):
	_inherit = "report_vat_report"

	date_from = fields.Datetime('Start Date', required=True)
	date_to = fields.Datetime('End Date', required=True)

VATReportInherit()
