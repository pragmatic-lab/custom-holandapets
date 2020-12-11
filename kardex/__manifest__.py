# -*- encoding: utf-8 -*-

{
	'name' : 'Kardex',
	'version' : '1.0',
	'category': 'Custom',
	'description': """Modulo para reporte de kardex""",
	'author': 'Rodrigo Fernandez',
	'website': 'http://aquih.com/',
	'depends' : [ 'stock' ],
	'data' : [
		'security/ir.model.access.csv',
		'views/report.xml',
		'views/reporte_kardex.xml',
		'views/report_stockinventory.xml',
		'views/report_kardex_lines_view.xml',

	],
	'installable': True,
	'certificate': '',
}
