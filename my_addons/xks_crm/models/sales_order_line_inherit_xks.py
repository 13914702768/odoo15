# -*- coding: utf-8 -*-

from odoo import api, fields, models

class SalesOrderLineInheritXks(models.Model):
    _inherit = 'sale.order.line'

    x_remark = fields.Char(string='Remark') # 备注

    product_model = fields.Char(string='Product Model', related='product_id.default_code')  # 内部型号
    product_external_model = fields.Char(string='Product Model', related='product_id.external_model')  # 外部型号

    optional_configure = fields.Char(string='Optional Configure', compute='_compute_product_detail')  # 选配

    @api.depends('product_id')
    def _compute_product_detail(self):
        for line in self:
            variant = line.product_id.product_template_attribute_value_ids._get_combination_name()
            if variant:
                line.optional_configure = variant
            else:
                line.optional_configure = None

    # 销售订单中订单行中数量发生变化
    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id,
                quantity=self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            sale_price_unit = product._get_tax_included_unit_price(
                    self.company_id or self.order_id.company_id,
                    self.order_id.currency_id,
                    self.order_id.date_order,
                    'sale',
                    fiscal_position=self.order_id.fiscal_position_id,
                    product_price_unit=self._get_display_price(product),
                    product_currency=self.order_id.currency_id
                )
            if sale_price_unit == self.price_unit:
                self.price_unit = sale_price_unit
            else:
                 pass