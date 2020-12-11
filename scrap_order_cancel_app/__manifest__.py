# -*- coding: utf-8 -*-
{
    'name': 'Cancel Scrap Order in Odoo',
    "author": "Edge Technologies",
    'version': '12.0.1.2',
    'live_test_url': "https://youtu.be/qpO6_MyuaPA",
    "images":['static/description/main_screenshot.png'],
    'summary': 'This apps helps user to cancel validated scrap order and set to reset as draft or delete scrap order.',
    'description': """
                    This modules helps to Cancel Scrap Order.
  This modules helps to Cancel Scrap Order cancel scrap order  cancelling scrap order cancelling order scrap order cancelling
raw material scrap order cancel Waste Materials on Job Order cancel scrap order cancel waste job order cancel job order Waste Management Quality Control MRP scrap order cancelling waste order canceling Scrap Report scrap material scrap product cancel material order cancel scrap order cancelling order cancel product scrap cancel scrap product order cancel validated Scrap Order validated cancel scrap order Stock Scrapping
Inventory Backdate 
    """,
    'depends': ['base','sale_management','account','stock','purchase','account_cancel','stock_account'],
    'data': [
            "security/ir.model.access.csv",
            "security/scrap_security.xml",
            "views/scrap_view.xml"
            ],
    'installable': True,
    'auto_install': False,
    'price': 18,
    'currency': "EUR",
    'category': 'Warehouse',
}