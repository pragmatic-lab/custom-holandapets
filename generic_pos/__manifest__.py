{
    'name': "Mejoras en POS",
    'version': '1.0.0.0',
    "author" : "Carlos López Mite",
    "website": "https://blaze-otp.com",
    'category': 'Point Of Sale',
    'description': """
        Mejoras en POS
    """,
    'depends': [
        'point_of_sale',
        'generic_stock',
        'generic_stock_account',
        'odoo_utils',
        'stock_picking_invoice_link',
    ],
    'data': [
        'data/module_category_data.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/menu_root.xml',
        'views/report_pos_order_view.xml',
        'views/report_pos_payment_view.xml',
        'views/product_template_view.xml',
        'views/pos_category_view.xml',
        'views/pos_order_view.xml',
        'views/pos_session_view.xml',
        'views/pos_config_view.xml',
        'views/pos_cashbox_view.xml',
        'views/generic_pos_assets.xml',
    ],
    'installable': True,
    'auto_install': True,
}
