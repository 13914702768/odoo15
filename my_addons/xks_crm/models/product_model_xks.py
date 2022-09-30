# -*- coding: utf-8 -*-

from odoo import api, fields, models

class ProductModelXks(models.Model):
    _name = 'product.model'
    _description = 'Product Model'

    name = fields.Text(string='Description', required=True)
    code = fields.Char(string='Code', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    code_external = fields.Char(string='Code External', required=True)

    product_id = fields.Many2one('product.product', string='Product Model',
        change_default=True, ondelete='restrict', check_company=True)  # 产品型号


    @api.depends('name', 'code', 'code_external')
    def name_get(self):
        result = []
        show_type = self.env.context.get('default_show_type', False)
        for model in self:
            if show_type == '1':
                name = self.code
            else:
                name = self.code_external
            result.append((model.id, name))
        return result