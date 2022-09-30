# -*- coding: utf-8 -*-

from odoo import api, fields, models

class LeadsPlanXks(models.Model):
    _name = 'crm.lead.plan'
    _description = 'Leads Plan'

    lead_id = fields.Many2one('crm.lead', string='Lead Reference', required=True, ondelete='cascade', index=True, copy=False)

    product_name = fields.Char(string='Product Name')
    product_model = fields.Char(string='Product Model')
    product_qty = fields.Integer(string='Buy Quantity')
    price_unit = fields.Float(string='Unit Price', required=True, digits='Product Price')
    currency_id = fields.Many2one('res.currency', 'Currency', required=True, default=2)
    remark = fields.Text(string='Remark')
