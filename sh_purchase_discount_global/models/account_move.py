from odoo import fields, models, api, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError


class AccountMove(models.Model):
    _inherit = 'account.move'

    discount_method = fields.Selection([("fixed", "Fixed"),
                                        ("percentage", "Percentage")])
    discount_amount = fields.Float()
    order_discount = fields.Float("- Discount", compute="_compute_amount")
    sh_final_amount = fields.Monetary(compute="_compute_amount")
    amount_total = fields.Monetary(string='Total',
                                   store=True,
                                   readonly=True,
                                   compute='_compute_amount',
                                   inverse='_inverse_amount_total')

    def _recompute_dynamic_lines(self,
                                 recompute_all_taxes=False,
                                 recompute_tax_base_amount=False):
        ''' Recompute all lines that depend of others.

        For example, tax lines depends of base lines (lines having tax_ids set). This is also the case of cash rounding
        lines that depend of base lines or tax lines depending the cash rounding strategy. When a payment term is set,
        this method will auto-balance the move with payment term lines.

        :param recompute_all_taxes: Force the computation of taxes. If set to False, the computation will be done
                                    or not depending of the field 'recompute_tax_line' in lines.
        '''
        res = super(AccountMove,
                    self)._recompute_dynamic_lines(recompute_all_taxes,
                                                   recompute_tax_base_amount)

        for invoice in self:
            if invoice.order_discount > 0:
                if not invoice.company_id.sh_po_discount_account_id:
                    raise UserError("Please set Discount Account!!")

                debit_line = False
                credit_line = False
                account_id = invoice.partner_id.property_account_payable_id.id

                for line in invoice.line_ids:
                    if line.account_id.id == account_id:
                        if line.debit > 0:
                            line.debit = invoice.sh_final_amount
                            debit_line = True

                        if line.credit > 0:
                            line.credit = invoice.sh_final_amount
                            credit_line = True

                sh_round_line = invoice.line_ids.filtered(
                    lambda x: x.account_id.id == invoice.company_id.
                    sh_po_discount_account_id.id)
                invoice.line_ids -= sh_round_line

                if debit_line:
                    create_method = self.env[
                        'account.move.line'].new or self.env[
                            'account.move.line'].create
                    sh_rounding_line = create_method({
                        'account_id':
                        invoice.company_id.sh_po_discount_account_id.id,
                        'debit':
                        invoice.order_discount,
                        'credit':
                        0.0,
                        'name':
                        'Discount Amount',
                        'exclude_from_invoice_tab':
                        True,
                        'is_rounding_line':
                        False,
                        # 'account_internal_type':'receivable',
                    })

                    invoice.line_ids += sh_rounding_line

                if credit_line:
                    create_method = self.env[
                        'account.move.line'].new or self.env[
                            'account.move.line'].create
                    sh_rounding_line = create_method({
                        'account_id':
                        invoice.company_id.sh_po_discount_account_id.id,
                        'debit':
                        0.0,
                        'credit':
                        invoice.order_discount,
                        'name':
                        'Discount Amount',
                        'exclude_from_invoice_tab':
                        True,
                        'is_rounding_line':
                        False,
                        # 'account_internal_type':'receivable',
                    })

                    invoice.line_ids += sh_rounding_line

        return res

    @api.depends(
        'line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.debit', 'line_ids.credit', 'line_ids.currency_id',
        'line_ids.amount_currency', 'line_ids.amount_residual',
        'line_ids.amount_residual_currency', 'line_ids.payment_id.state',
        'line_ids.full_reconcile_id')
    def _compute_amount(self):
        for move in self:

            if move.payment_state == 'invoicing_legacy':
                # invoicing_legacy state is set via SQL when setting setting field
                # invoicing_switch_threshold (defined in account_accountant).
                # The only way of going out of this state is through this setting,
                # so we don't recompute it here.
                move.payment_state = move.payment_state
                continue

            total_untaxed = 0.0
            total_untaxed_currency = 0.0
            total_tax = 0.0
            total_tax_currency = 0.0
            total_to_pay = 0.0
            total_residual = 0.0
            total_residual_currency = 0.0
            total = 0.0
            total_currency = 0.0
            order_discount = 0.0
            currencies = move._get_lines_onchange_currency().currency_id

            for line in move.line_ids:
                if move.is_invoice(include_receipts=True):
                    # === Invoices ===

                    if not line.exclude_from_invoice_tab:
                        # Untaxed amount.
                        total_untaxed += line.balance
                        total_untaxed_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.tax_line_id:
                        # Tax amount.
                        total_tax += line.balance
                        total_tax_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.account_id.user_type_id.type in ('receivable',
                                                               'payable'):
                        # Residual amount.
                        total_to_pay += line.balance
                        total_residual += line.amount_residual
                        total_residual_currency += line.amount_residual_currency
                else:
                    # === Miscellaneous journal entry ===
                    if line.debit:
                        total += line.balance
                        total_currency += line.amount_currency

            if move.move_type == 'entry' or move.is_outbound():
                sign = 1
            else:
                sign = -1
            move.amount_untaxed = sign * (total_untaxed_currency if len(
                currencies) == 1 else total_untaxed)
            move.amount_tax = sign * (total_tax_currency
                                      if len(currencies) == 1 else total_tax)
            move.amount_total = sign * (total_currency
                                        if len(currencies) == 1 else total)
            move.amount_residual = -sign * (total_residual_currency if len(
                currencies) == 1 else total_residual)
            move.amount_untaxed_signed = -total_untaxed
            move.amount_tax_signed = -total_tax
            move.amount_total_signed = abs(
                total) if move.move_type == 'entry' else -total
            move.amount_residual_signed = total_residual

            if move.discount_method == 'fixed':
                order_discount = move.discount_amount

            if move.discount_method == 'percentage':
                if move.company_id.discount_applies_on == 'untax_amount':
                    order_discount = (move.amount_untaxed *
                                      move.discount_amount) / 100
                else:
                    order_discount = (move.amount_untaxed + move.amount_tax
                                      ) * (move.discount_amount / 100)

            move.order_discount = order_discount
            move.sh_final_amount = move.amount_total - order_discount

            currency = len(
                currencies) == 1 and currencies or move.company_id.currency_id

            # Compute 'payment_state'.
            new_pmt_state = 'not_paid' if move.move_type != 'entry' else False

            if move.is_invoice(
                    include_receipts=True) and move.state == 'posted':

                if currency.is_zero(move.amount_residual):
                    reconciled_payments = move._get_reconciled_payments()
                    if not reconciled_payments or all(
                            payment.is_matched
                            for payment in reconciled_payments):
                        new_pmt_state = 'paid'
                    else:
                        new_pmt_state = move._get_invoice_in_payment_state()
                elif currency.compare_amounts(total_to_pay,
                                              total_residual) != 0:
                    new_pmt_state = 'partial'

            if new_pmt_state == 'paid' and move.move_type in ('in_invoice',
                                                              'out_invoice',
                                                              'entry'):
                reverse_type = move.move_type == 'in_invoice' and 'in_refund' or move.move_type == 'out_invoice' and 'out_refund' or 'entry'
                reverse_moves = self.env['account.move'].search([
                    ('reversed_entry_id', '=', move.id),
                    ('state', '=', 'posted'), ('move_type', '=', reverse_type)
                ])

                # We only set 'reversed' state in cas of 1 to 1 full reconciliation with a reverse entry; otherwise, we use the regular 'paid' state
                reverse_moves_full_recs = reverse_moves.mapped(
                    'line_ids.full_reconcile_id')
                if reverse_moves_full_recs.mapped(
                        'reconciled_line_ids.move_id').filtered(
                            lambda x: x not in
                            (reverse_moves + reverse_moves_full_recs.mapped(
                                'exchange_move_id'))) == move:
                    new_pmt_state = 'reversed'

            move.payment_state = new_pmt_state
