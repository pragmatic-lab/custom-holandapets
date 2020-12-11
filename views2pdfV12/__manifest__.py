# coding: utf-8
# Odoo 12

{
    'name': 'views2pdf',
    'version': '12',
    'author': 'Captivea',
    'website': 'http://www.captivea.com/',
    'license': 'AGPL-3',
    'description': """
Generate PDF from Views
=========================

This module will allow you to generate a pdf report from any views (FORM, TREE, KANBAN, PIVOT, GRAPH, Galendar) in Odoo v12.
Based on https://www.odoo.com/apps/modules/10.0/views2pdf/ by Abderrahmen Khalledi.

    """,
    'images': ['static/description/captivea_logo.png'],
    'depends': ['base', 'web'],
    'data': ['views/assets.xml'],
    'qweb': ['static/src/xml/view.xml'],
    'application': False,
    'auto_install': False,
    'installable': True,
}
