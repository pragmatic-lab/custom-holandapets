# -*- coding: utf-8 -*-
# Part of SnepTech. See LICENSE file for full copyright and licensing details.##
##################################################################################

{
    'name': 'Product Variants Pricelist',
    'version': '12.0.0.1',
    'sequence': 1,
    'summary': 'This app used to manage pricelist according to product variant',
    'author': 'SnepTech',
    'license': 'AGPL-3',
    'website': 'https://www.sneptech.com',
    'category': 'Sales',

    'description':"""
       
        How to set different pricelist for product variants? Difficult...!!!
        By default, The product variant price lists are not separated from variant to variant in product view.
        The price set on the product will be applicable for all the variants. So in order to overcome the problem and make easy configuration,
        Sneptech has created module to easily manage price lists by product variants.
    """,
    'depends':['sale_management'],
    'live_test_url':"https://youtu.be/sdPLmh-n69w",
    'data':[
        'views/product_view.xml',
        ],
        
    'price': '39.99',
    'currency': "USD",
    'installable': True,
    'auto_install': False,
    'application': True,
    "images":['static/description/Banner.png'],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
