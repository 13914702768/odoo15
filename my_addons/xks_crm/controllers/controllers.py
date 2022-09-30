# -*- coding: utf-8 -*-
from odoo import http


class XksCrm(http.Controller):
    @http.route('/xks_crm/xks_crm', auth='public')
    def index(self, **kw):
        #   http://localhost:8069/xks_crm/xks_crm?name=name
        name = kw.get('name')
        print(name)
        return "Hello, world"

    @http.route('/xks_crm/xks_crm/objects', auth='public')
    def list(self, **kw):
        return http.request.render('xks__crm.listing', {
            'root': '/xks__crm/xks__crm',
            'objects': http.request.env['xks__crm.xks__crm'].search([]),
        })

    @http.route('/xks_crm/xks_crm/objects/<model("xks_crm.xks_crm"):obj>', auth='public')
    def object(self, obj, **kw):
        return http.request.render('xks_crm.object', {
            'object': obj
        })
