# -*- coding: utf-8 -*-
from odoo import fields, models, api,_

class Rescompany(models.Model):
    _inherit = 'res.company'

    discount_applies_on = fields.Selection(
        [
            ("tax_amount", "Taxed Amount"),
            ("untax_amount", "Untaxed Amount"),

        ],default = 'tax_amount',readonly=False)

    sh_po_discount_account_id = fields.Many2one(
        'account.account', string="Discount Account")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    discount_applies_on = fields.Selection(
        [
            ("tax_amount", "Tax Amount"),
            ("untax_amount", "Untax Amount"),

        ], related="company_id.discount_applies_on",readonly=False)

    sh_po_discount_account_id = fields.Many2one('account.account',
                                             related='company_id.sh_po_discount_account_id', string="Discount Account", readonly=False)
