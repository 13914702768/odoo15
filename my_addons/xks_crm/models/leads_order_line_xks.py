# -*- coding: utf-8 -*-

from odoo import api, fields, models

class LeadsOrderLineXks(models.Model):
    _name = 'crm.lead.order.line'
    _description = 'Leads Order Line'

    lead_id = fields.Many2one('crm.lead', string='Lead Reference', required=True, ondelete='cascade', index=True, copy=False)
    name = fields.Html(string='Product Description')
    sequence = fields.Integer(string='Sequence', default=10)

    product_id = fields.Many2one(
        'product.product', string='Product',
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        change_default=True, ondelete='restrict', check_company=True) # 产品
    product_template_id = fields.Many2one(
        'product.template', string='Product Template',
        related="product_id.product_tmpl_id", domain=[])

    company_id = fields.Many2one(related='lead_id.company_id', string='Company', store=True, index=True)

    buy_number = fields.Integer(string='Buy Number', default=1) # 购买数量
    
    price_unit = fields.Float(related='product_id.lst_price', readonly=True, string='Price Unit')

    application_scenes = fields.Char(string='Application Scenarios') # 应用场景
                                                 
    product_model = fields.Char(string='Product Model', related='product_id.default_code') # 内部型号
    product_external_model = fields.Char(string='Product Model', related='product_id.external_model') # 外部型号

    optional_configure = fields.Char(string='Optional Configure', compute='_compute_product_detail') #选配

    @api.depends('product_id')
    def _compute_product_detail(self):
        for line in self:
            variant = line.product_id.product_template_attribute_value_ids._get_combination_name()
            if variant:
                 line.optional_configure = variant
            else:
                line.optional_configure = None

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        return lines

    def write(self, values):
        result = super(LeadsOrderLineXks, self).write(values)
        return result