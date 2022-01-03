odoo.define('payment_paguelofacil.payment_form', require => {
    "use strict";
    const PaymentForm = require('payment.payment_form');
    PaymentForm.include({
        _get_redirect_form_method() {
            const checked_radio = this.$('input[type="radio"]:checked')
            if (checked_radio.length === 1 && checked_radio[0].dataset.provider === 'paguelofacil') {
                return 'get';
            } else {
                return this._super(...arguments)
            }
        }
    })
    return PaymentForm
})