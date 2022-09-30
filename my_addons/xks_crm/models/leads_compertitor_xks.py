# -*- coding: utf-8 -*-

from odoo import api, fields, models

class LeadsCompetitorXks(models.Model):
    _name = 'crm.lead.competitor'
    _description = 'Leads Competitor'

    lead_id = fields.Many2one('crm.lead', string='Lead Reference', required=True, ondelete='cascade', index=True, copy=False)

    sequence = fields.Integer(string='Sequence', default=10)
    company_name = fields.Char(string='Company Name', required=True)
    product_name = fields.Char(string='Product Name', required=True)
    product_model = fields.Char(string='Product Model', required=True)
    price = fields.Float(string='Price')
    remark = fields.Text(string='Remark')



