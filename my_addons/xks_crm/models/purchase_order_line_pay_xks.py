# -*- coding: UTF-8 -*-
from odoo import api, fields, models

class PurchaseOrderLinePayXks(models.Model):
    _name = 'purchase.order.line.pay.xks'
    _description = 'Purchase Order Line Pay'

    purchase_order_pay_id = fields.Many2one('purchase.order.pay.xks', string='Purchase Order Pay', required=True,
                                            ondelete='cascade', index=True, copy=False)  # 支付订单
    purchase_order_line_id = fields.Many2one('purchase.order.line', string='Purchase Order Line'
                                             ,domain="[('order_id.id', '=', purchase_order)]") # 采购订单行
    purchase_order = fields.Integer(string='Purchase Order', default=lambda self: self.env.context.get('purchase_order_id', False) ) # 采购订单
    product_qty = fields.Float(related='purchase_order_line_id.product_qty') # 采购订单数量
    price_unit = fields.Float(related='purchase_order_line_id.price_unit') #采购订单单价

    payment_qty = fields.Float(string='Current Pay Quantity') # 当前支付数量
    price_pay = fields.Float(string='Current Pay Price') # 当前支付金额

    unpaid_qty = fields.Float(string='Unpaid Quantity', compute='_compute_unpaid') #未支付数量
    price_unpaid = fields.Float(string='Unpaid Price', compute='_compute_unpaid')

    # price_subtotal = fields.Float(string='Subtotal') # 小计

    @api.depends('payment_qty', 'product_qty')
    def _compute_unpaid(self):
        for payline in self:
            total_qty = 0.0;
            total_price_pay = 0.0
            if payline.purchase_order_pay_id.pay_project == '1':
                # 查询支付订单行中此产品支付列表
                pays = self.env['purchase.order.pay.xks'].search([
                    ('purchase_order_id', '=', payline.purchase_order)
                ])
                if pays:
                    for pay in pays:
                        payline.unpaid_qty = payline.unpaid_qty
                        payline.price_unpaid = payline.price_unpaid
                        for purchase_order_line in pay.purchase_order_line_pay_ids:
                            if purchase_order_line.purchase_order_line_id == payline.purchase_order_line_id:
                                # 订单行所有支付的预付款和数量
                                total_price_pay = total_price_pay + purchase_order_line.price_pay
                                if pay.pay_project == '1':
                                    total_qty = total_qty + purchase_order_line.payment_qty
                                # 剩余价格为单价*数量-已支付价格-当前要支付价格
                                payline.unpaid_qty = payline.product_qty - total_qty
                                payline.price_unpaid = payline.product_qty * payline.price_unit - total_price_pay
                else:
                    payline.unpaid_qty = payline.product_qty
                    payline.price_unpaid = payline.product_qty * payline.price_unit
            # elif payline.purchase_order_pay_id.pay_project == '2':
            #     payline.unpaid_qty = payline.unpaid_qty
            #     payline.price_unpaid = payline.price_unpaid
            #     pass
            else:
                # 查询支付订单行中此产品支付列表
                pays = self.env['purchase.order.pay.xks'].search([
                    ('purchase_order_id', '=', payline.purchase_order)
                ])
                if pays:
                    for pay in pays:
                        payline.unpaid_qty = payline.unpaid_qty
                        payline.price_unpaid = payline.price_unpaid
                        if len(pay.purchase_order_line_pay_ids.ids) > 0:
                            # 支付表的订单行等于当前订单行
                            for purchase_order_line in pay.purchase_order_line_pay_ids:
                                if purchase_order_line.purchase_order_line_id == payline.purchase_order_line_id:
                                    total_price_pay = total_price_pay + purchase_order_line.price_pay
                                    if pay.pay_project == '3':
                                        total_qty = total_qty + purchase_order_line.payment_qty
                                    payline.unpaid_qty = payline.product_qty - total_qty
                                    payline.price_unpaid = payline.product_qty * payline.price_unit - total_price_pay
                        else:
                            payline.unpaid_qty = payline.product_qty - total_qty
                            payline.price_unpaid = payline.product_qty * payline.price_unit - total_price_pay
                else:
                    payline.unpaid_qty = payline.product_qty
                    payline.price_unpaid = payline.product_qty * payline.price_unit


    @api.onchange('payment_qty', 'price_unit')
    def _onchange_payment_qty(self):
        for payline in self:
            if payline.payment_qty > 0:
                payline.price_pay = payline.payment_qty * payline.price_unit * float(payline.purchase_order_pay_id.percentage)


