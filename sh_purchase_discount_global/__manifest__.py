# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name":
    "Purchase Discount Global",
    "author":
    "Softhealer Technologies",
    "website":
    "https://www.softhealer.com",
    "support":
    "support@softhealer.com",
    "category":
    "Purchase",
    "summary":
    "",
    "description":
    """""",
    "version":
    "14.0.1",
    "depends": ["purchase"],
    "application":
    True,
    "data": [
        'security/discount_security.xml',
        'views/purchase_config_settings.xml',
        'views/purchase_order.xml',
        'views/account_move.xml',
        'report/po_report.xml',
    ],
    "images": [
        "",
    ],
    "auto_install":
    False,
    "installable":
    True,
    "price":
    50,
    "currency":
    "EUR"
}
