# -*- coding: utf-8 -*-
import logging
import pprint
import werkzeug

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class PaguelofacilController(http.Controller):
    _return_url = '/payment/paguelofacil/return/'

    @http.route(['/payment/paguelofacil/return', ], type='http', auth='public', csrf=False)
    def paguelofacil_return(self, **get):
        _logger.info('Beginning Paguelofacil form_feedback with get data %s', pprint.pformat(get))
        request.env['payment.transaction'].sudo().form_feedback(get, 'paguelofacil')
        return werkzeug.utils.redirect('/payment/process')