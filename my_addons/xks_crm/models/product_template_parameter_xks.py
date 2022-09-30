# -*- coding: utf-8 -*-

from odoo import api, fields, models

class ProductTemplateParameterXks(models.Model):
    _name = 'product.template.parameter.xks'
    _description = 'Product Template Parameter'

    product_template_id = fields.Many2one('product.template', string='Product Template', required=True, ondelete='cascade', index=True, copy=False)

    parameter_name = fields.Char(string='Parameter Name')
    parameter_value = fields.Char(string='Parameter Value')
    parameter_unit = fields.Char(string='Parameter Unit')
    remark = fields.Text(string='Remark')
    sequence = fields.Integer(string='Sort', default=10)



