# -*- coding: UTF-8 -*-
from odoo import api, fields, models


class ProductTemplateInheritXks(models.Model):
    _inherit = "product.template"

    middle_quote = fields.Float(string='Middle Quote', digits='Product Price', default=1.0)

    reserve_quote = fields.Float(string='Reserve Quote', digits='Product Price', default=1.0)
    
    parameter_ids = fields.One2many('product.template.parameter.xks', 'product_template_id',
                                    string='Parameters', copy=True, auto_join=True)
