# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2015 Dynexcel (<http://dynexcel.com/>).
#
##############################################################################
{
    'name': 'Partner Ledger',
    'version': '1.1',
    'summary': 'This module will add Partner Ledger Report',
    'description': 'This module provides the movement of individual products with opening and closing stocks',
    'author': 'Dynexcel',
    'maintainer': 'Dynexcel',
    'company': 'Dynexcel',
    'website': 'https://www.dynexcel.com',
    'depends': [
		'base', 'account',
		],
    'category': 'Accounting',
    'demo': [],
    'data': ['views/partner_ledger_views.xml',
             'security/ir.model.access.csv',
             'report/partner_ledger_report.xml',
             'report/partner_ledger_report_template.xml'],
    'installable': True,
    'images': ['static/description/banner.png'],
    'qweb': [],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
    'live_test_url':'https://youtu.be/5OqXXKO6gRA',
}
