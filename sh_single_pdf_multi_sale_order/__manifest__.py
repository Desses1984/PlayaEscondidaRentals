# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "Merge Multiple Sale Order PDF",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "license": "OPL-1",
    "support": "support@softhealer.com",
    "category": "Sales",
    "summary": """
Merge Sale Orders,
""",
    "description": """
This module useful to Merge Sale Orders.
""",
    "version": "14.0.1",
    "depends": [
        "sale_management",'stock',
    ],
    "application": True,
    "data": [    
        "views/report_action.xml",
        "report/merge_report.xml",
    ],
    "images": ["static/description/background.png", ],
    "live_test_url": "https://youtu.be/o7xQRAyvRRw",
    "auto_install": False,
    "installable": True,
    "price": 25,
    "currency": "EUR"
}
