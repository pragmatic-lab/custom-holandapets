# -*- coding: utf-8 -*-
{
    # App information
    'name': 'Tax Report in Excel',
    'version': '12.0',
    'category': 'Stock',
    'summary': 'Using this App, one can Print Tax Report in Excel in Odoo.',
    'license': 'OPL-1',
    
     
    # Dependencies
    'depends': ['account'],
    
    # Views
    'data': [
       'views/account_tax_menu.xml'
        ],
        
    # Odoo Store Specific
    'images': ['static/description/Text-Report-in-Excel-Store-Cover.jpg'],  
    
    # Author

    'author': 'Emipro Technologies Pvt. Ltd.',
    'website': 'http://www.emiprotechnologies.com',
    'maintainer': 'Emipro Technologies Pvt. Ltd.',
    
        
    'installable': True,
    'auto_install': False,
    'application':True,
    'sequence':1,
    'live_test_url':'https://www.emiprotechnologies.com/free-trial?app=account-tax-report-ept&version=12&edition=enterprise',
    'price': '49',
    'currency': 'EUR',
}
