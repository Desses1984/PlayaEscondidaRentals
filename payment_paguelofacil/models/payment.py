# -*- coding: utf-8 -*-
import json
import logging
import time

import requests
from werkzeug import urls

from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.addons.payment_paguelofacil.controllers.main import PaguelofacilController
from odoo.http import request

_logger = logging.getLogger(__name__)

PAGUELOFACIL_PRODUCTION_URL = 'https://secure.paguelofacil.com'
PAGUELOFACIL_TESTING_URL = 'https://sandbox.paguelofacil.com'


class PaymentAcquirerPaguelofacil(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(
        selection_add=[('paguelofacil', 'Paguelofacil')], ondelete={'paguelofacil': 'set default'})
    paguelofacil_cclw = fields.Char('CCLW', required_if_provider='paguelofacil', groups='base.group_user')

    def _get_paguelofacil_url(self):
        return PAGUELOFACIL_PRODUCTION_URL if self.state == 'enabled' else PAGUELOFACIL_TESTING_URL

    def paguelofacil_form_generate_values(self, values):
        base_url = self.get_base_url()
        data = {
            'CCLW': self.paguelofacil_cclw,
            'CMTN': values.get('amount', 0),
            'CDSC': values.get('reference'),
            'RETURN_URL': urls.url_join(base_url, PaguelofacilController._return_url),
            'reference': values.get('reference'),
        }
        generate_url = f'{self._get_paguelofacil_url()}/LinkDeamon.cfm'
        response = requests.post(generate_url, data)

        paguelofacil_response = response.json()
        if paguelofacil_response['success']:
            response_data = paguelofacil_response['data']
            return {
                'response_data': response_data
            }
        else:
            raise ValidationError(_("Error trying to generate paguelofacil redirect url. The server sent us: %s",
                                    paguelofacil_response['headerStatus']))


class PaymentTxPaguelofacil(models.Model):
    _inherit = 'payment.transaction'

    # --------------------------------------------------
    # FORM RELATED METHODS
    # --------------------------------------------------
    @api.model
    def _paguelofacil_form_get_tx_from_data(self, data):
        reference = data.get('reference')
        if not reference:
            _logger.info('Paguelofacil: received data with missing reference (%s)' % reference)
            raise ValidationError(_('Paguelofacil: received data with missing reference (%s)', reference))

        txs = self.env['payment.transaction'].search([('reference', '=', reference)])
        if not txs or len(txs) > 1:
            error_msg = _('Paguelofacil: received data for reference %s', reference)
            logger_msg = 'Paguelofacil: received data for reference %s' % reference
            if not txs:
                error_msg += _('; no order found')
                logger_msg += '; no order found'
            else:
                error_msg += _('; multiple order found')
                logger_msg += '; multiple order found'
            _logger.info(logger_msg)
            raise ValidationError(error_msg)
        return txs

    def _paguelofacil_form_get_invalid_parameters(self, data):
        return []

    def _paguelofacil_form_validate(self, data):
        if self.state in ['done']:
            _logger.info('Paguelofacil: trying to validate an already validated tx (ref %s)', self.reference)
            return True

        status = data.get('Estado')
        res = {
            'acquirer_reference': data.get('Oper'),
        }
        if status == 'Aprobada':
            _logger.info('Validated Paguelofacil payment for tx %s: set as done' % self.reference)
            date_validate = fields.Datetime.now()
            res.update(date=date_validate)
            self._set_transaction_done()
            self.write(res)
            self.execute_callback()
            return True
        elif status == 'Denegada':
            _logger.info('Received notification for Paguelofacil payment %s: set as Canceled' % self.reference)
            res.update(state_message=data.get('Razon', ''))
            self._set_transaction_cancel()
            return self.write(res)
        else:
            error = 'Received unrecognized status for Paguelofacil payment %s: %s, set as error' % (self.reference, status)
            _logger.info(error)
            res.update(state_message=error)
            self._set_transaction_error()
            return self.write(res)
