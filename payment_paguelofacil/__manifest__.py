# -*- coding: utf-8 
{
    'name': 'Paguelofacil Payment Acquirer',
    'version': '2.0',
    'depends': [
        'payment',
    ],
    'external_dependencies': {},
    'author': 'Eduweb Group',
    'website': 'https://www.eduwebgroup.com',
    'summary': """Paguelofacil Payment Acquirer""",
    'description': """
        Paguelofacil Payment Acquirer
    """,
    'category': 'Payment Acquirers',
    'data': [
        'views/assets.xml',
        'views/payment_views.xml',
        'views/payment_paguelofacil_templates.xml',
        'data/payment_acquirer_data.xml',
        'data/payment_icon_data.xml',
    ],
    'qweb': [],
    'css': [],
    'images': ['static/description/description.png'],
    'demo': [],
    'installable': True,
    'application': True,
    'post_init_hook': 'create_missing_journal_for_acquirers',
    'uninstall_hook': 'uninstall_hook',
    'price': 50,
    'curreny': 'USD',
    'license': 'OPL-1',
}
