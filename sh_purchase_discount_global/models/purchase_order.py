# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.float_utils import float_is_zero
from odoo.tools.misc import formatLang, get_lang
from itertools import groupby


class ShPurchaseOrderLine(models.Model):

    _inherit = "purchase.order.line"

    discount = fields.Float(digits='Discount', default=0.0)

    @api.depends('product_qty', 'price_unit', 'taxes_id', 'discount')
    def _compute_amount(self):
        for line in self:
            vals = line._prepare_compute_all_values()
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.taxes_id.compute_all(price, vals['currency_id'],
                                              vals['product_qty'],
                                              vals['product'], vals['partner'])

            line.update({
                'price_tax':
                sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total':
                taxes['total_included'],
                'price_subtotal':
                taxes['total_excluded'],
            })

    def _prepare_account_move_line(self, move=False):
        self.ensure_one()
        res = {
            'display_type': self.display_type,
            'sequence': self.sequence,
            'name': '%s: %s' % (self.order_id.name, self.name),
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': self.qty_to_invoice,
            'price_unit': self.price_unit,
            'discount': self.discount,
            'tax_ids': [(6, 0, self.taxes_id.ids)],
            'analytic_account_id': self.account_analytic_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'purchase_line_id': self.id,
        }
        if not move:
            return res

        if self.currency_id == move.company_id.currency_id:
            currency = False
        else:
            currency = move.currency_id

        res.update({
            'move_id': move.id,
            'currency_id': currency and currency.id or False,
            'date_maturity': move.invoice_date_due,
            'partner_id': move.partner_id.id,
        })
        return res


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    discount_type = fields.Selection([('line_discount', "Discount On Line"),
                                      ("global_discount", "Global Discount")],
                                     default="global_discount")

    discount_method = fields.Selection([("fixed", "Fixed"),
                                        ("percentage", "Percentage")])
    discount_amount = fields.Float()
    order_discount = fields.Float("- Discount", compute='_amount_all')

    @api.onchange('discount_type')
    def _onchange_discount_type(self):
        if self:
            if self.discount_type == "line_discount":
                self.discount_method = False
                self.discount_amount = 0.0
            if self.discount_type == "global_discount":
                if self.order_line:
                    for line in self.order_line:
                        line.discount = 0.0

    @api.depends('order_line.price_total', 'order_line.price_tax',
                 'discount_method', 'discount_amount')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = order_discount = 0.0

            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax

            if order.discount_method == 'fixed':
                order_discount = order.discount_amount

            if order.discount_method == 'percentage':
                if order.company_id.discount_applies_on == 'untax_amount':
                    order_discount = (amount_untaxed *
                                      order.discount_amount) / 100
                else:
                    order_discount = (amount_untaxed + amount_tax) * (
                        order.discount_amount / 100)

            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed - order_discount + amount_tax,
                'order_discount': order_discount
            })

    def _prepare_invoice(self):
        """Prepare the dict of values to create the new invoice for a purchase order.
        """
        self.ensure_one()
        move_type = self._context.get('default_move_type', 'in_invoice')
        journal = self.env['account.move'].with_context(
            default_move_type=move_type)._get_default_journal()
        if not journal:
            raise UserError(
                _('Please define an accounting purchase journal for the company %s (%s).'
                  ) % (self.company_id.name, self.company_id.id))

        partner_invoice_id = self.partner_id.address_get(['invoice'
                                                          ])['invoice']
        invoice_vals = {
            'ref':
            self.partner_ref or '',
            'move_type':
            move_type,
            'narration':
            self.notes,
            'currency_id':
            self.currency_id.id,
            'invoice_user_id':
            self.user_id and self.user_id.id or self.env.user.id,
            'partner_id':
            partner_invoice_id,
            'fiscal_position_id':
            (self.fiscal_position_id
             or self.fiscal_position_id.get_fiscal_position(partner_invoice_id)
             ).id,
            'payment_reference':
            self.partner_ref or '',
            'partner_bank_id':
            self.partner_id.bank_ids[:1].id,
            'invoice_origin':
            self.name,
            'invoice_payment_term_id':
            self.payment_term_id.id,
            'invoice_line_ids': [],
            'company_id':
            self.company_id.id,
            'discount_method':
            self.discount_method,
            'discount_amount':
            self.discount_amount,
            # 'order_discount':self.order_discount,
            # 'sh_final_amount':self.amount_total,
        }
        return invoice_vals
