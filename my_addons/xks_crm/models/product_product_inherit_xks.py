# -*- coding: UTF-8 -*-
from odoo import api, fields, models


class ProductPorductInheritXks(models.Model):
    _inherit = "product.product"

    m_quote = fields.Float('Middle Quote', compute='_compute_product_f_quote',
                           digits='Product Price', inverse='_set_product_first_quote')

    r_quote = fields.Float('Reserve Quote', compute='_compute_product_f_quote',
                           digits='Product Price', inverse='_set_product_first_quote')

    external_model = fields.Char(string='External Model')

    @api.onchange('m_quote')
    def _set_product_first_quote(self):
        for product in self:
            if self._context.get('uom'):
                mvalue = self.env['uom.uom'].browse(self._context['uom'])._compute_price(product.middle_quote, product.uom_id)
                rvalue = self.env['uom.uom'].browse(self._context['uom'])._compute_price(product.reserve_quote, product.uom_id)
            else:
                mvalue = product.m_quote
                rvalue = product.r_quote
            mvalue -= product.price_extra
            rvalue -= product.price_extra
            product.write({'middle_quote': mvalue})
            product.write({'reserve_quote': rvalue})


    @api.depends('price_extra', 'middle_quote')
    @api.depends_context('uom')
    def _compute_product_f_quote(self):
        to_uom = None
        if 'uom' in self._context:
            to_uom = self.env['uom.uom'].browse(self._context['uom'])

        for product in self:
            if to_uom:
                middle_quote = product.uom_id._compute_price(product.middle_quote, to_uom)
                reserve_quote = product.uom_id._compute_price(product.reserve_quote, to_uom)
            else:
                middle_quote = product.middle_quote
                reserve_quote = product.reserve_quote
            product.m_quote = middle_quote + product.price_extra
            product.r_quote = reserve_quote + product.price_extra

    # @api.model_create_multi
    # def create(self, vals_list):
    #     lines = super().create(vals_list)
    #     return lines
    
    # def write(self, values):
    #     result = super(ProductPorductInheritXks, self).write(values)
    #     return result
    