{
    'name': 'Utilities',
    'version': '1.0.0.0',
    'category': 'Utilities',
    'description': """
""",
    'author': 'Carlos Lopez Mite(celm1990@hotmail.com)',
    'external_dependencies': {
        'python': [
        ]
    },
    'depends': [
        'base',
        'base_setup',
        'auth_signup',
        'mail',
        'web',
        'account',
        'product',
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/report_paperformat.xml',
        'wizard/wizard_messages_view.xml',
        'wizard/wizard_correct_record_view.xml',
        'wizard/wizard_product_no_stock_view.xml',
        'wizard/wizard_change_product_attribute_view.xml',
        'wizard/wizard_split_document_manual_view.xml',
        'views/odoo_utils_assets.xml',
        'views/ftp_config_view.xml',
    ],
    'installable': True,
    'auto_install': True,
}
