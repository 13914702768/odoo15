# -*- coding: UTF-8 -*-
from odoo import api, fields, models

SUPPLIER_TYPE = [
    ('1', 'Factory'),
    ('2', 'Freight Forwarding'),
]

SUPPLIER_STATE = [
    ('1', 'Qualified'),
    ('2', 'Failed'),
]


class CrmSupplierXks(models.Model):
    _name = 'crm.supplier.xks'
    _description = 'Supplier Xks'

    name = fields.Char(string='Supplier Name')
    country_id = fields.Many2one('res.country', string='Country', default=lambda self: 48)
    province_id = fields.Many2one('res.country.state', string='Province', domain="[('country_id','=', country_id)]")
    city_id = fields.Char(string='City')
    address = fields.Char(string='Address')
    contact_id = fields.Char(string='Contact')
    contact_dn = fields.Char(string='Contact Mobile')
    email = fields.Char(string='Email')
    wechat_number = fields.Char(string='WeChat Number')
    type_id = fields.Selection(SUPPLIER_TYPE, string='Type', index=True, default=SUPPLIER_TYPE[0][0])
    state_id = fields.Selection(SUPPLIER_STATE, string='State', index=True, default=SUPPLIER_STATE[0][0])