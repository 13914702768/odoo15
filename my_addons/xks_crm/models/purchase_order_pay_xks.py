# -*- coding: UTF-8 -*-
from odoo import api, fields, models

PAYMENT_PERCENTAGE = [
    ('0.1', '10%'),
    ('0.2', '20%'),
    ('0.3', '30%'),
    ('0.4', '40%'),
    ('0.5', '50%'),
    ('0.6', '60%'),
    ('0.7', '70%'),
    ('0.8', '80%'),
    ('0.9', '90%'),
    ('1.0', '100%'),
]

PAY_PROJECT = [
    ('1', '预付款'),
    ('2', '发货款'),
    ('3', '尾款'),
]

class PurchaseOrderPayXks(models.Model):
    _name = 'purchase.order.pay.xks'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Purchase Order Pay'

    name = fields.Char(string='Title')
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order',
                                             change_default=True, ondelete='restrict',
                                             default=lambda self: self.env.context.get('purchase_order_id', False),
                                             required=True)
    pay_project = fields.Selection(PAY_PROJECT, string='Pay Project', index=True, default=PAY_PROJECT[0][0], required=True)
    percentage = fields.Selection(PAYMENT_PERCENTAGE, string='Purchase Percentage', index=True, default=PAYMENT_PERCENTAGE[2][0])

    purchase_order_line_pay_ids = fields.One2many('purchase.order.line.pay.xks', 'purchase_order_pay_id',
                                                 string='Purchase Order Line Pay', copy=True, auto_join=True)

    remark = fields.Char(string='Remark')

    purchase_order_pay_invoice = fields.Html(string='Purchase Order Pay Invoice')

    purchase_pay_state = fields.Boolean(string='Purchase Pay State', default=False) # 采购单支付状态

    customer_pay_state = fields.Boolean(string='Customer Pay State', default=False) # 客户支付状态
    customer_advance_invoice = fields.Html(related='purchase_order_id.opportunity_id.x_advance_invoice')  # 商机中客户预付款支付单据
    customer_middle_invoice = fields.Html(related='purchase_order_id.opportunity_id.x_middle_invoice')  # 商机中客户发货款支付单据
    customer_balance_invoice = fields.Html(related='purchase_order_id.opportunity_id.x_balance_invoice')  # 商机中客户尾款款支付单据

    order_state = fields.Selection([('0', '初始状态'), ('1', '财务支付采购预付款'), ('2', '采购预付款支付成功'), ('3', '客户支付发货款'),
                                    ('4', '客户发货款审核'), ('5', '客户发货款审核通过'), ('6', '采购尾款已支付')], default='0') # 订单状态

    def write(self, vals):
        if self.pay_project == '1':
            # 财务支付供应商预付款
            if 'purchase_pay_state' in vals:
                if vals['purchase_pay_state']:
                    # 修改采购订单行当前为生产状态
                    purchase_order_lines = self.purchase_order_line_pay_ids.purchase_order_line_id
                    for line in purchase_order_lines:
                        line.current_state = '3'
                    # 删除支付预付款提醒
                    self.env['mail.activity'].sudo().search([
                        ('activity_type_id', '=', self.env['mail.activity.type'].search(
                                ['|', ('name', '=', '待办'), ('name', '=', 'To Do')]).id),
                        ('res_id', '=', self.id),
                        ('user_id', '=', self.env.user.id),
                        ('res_model_id', '=', self.env['ir.model']._get('purchase.order.pay.xks').id),
                        ('summary', '=', '您有一条采购订单待支付' if self.env.lang == 'zh_CN' else 'Purchase Order Advance Pay')
                    ]).unlink()
                    # 创建预付款支付成功提醒
                    self.env['mail.activity'].sudo().create({
                        'res_model_id': self.env['ir.model']._get('purchase.order').id,
                        'res_id': self.purchase_order_id.id,
                        'user_id': 9,
                        'activity_type_id': self.env['mail.activity.type'].search(['|', ('name', '=', '待办'), ('name', '=', 'To Do')]).id,
                        'summary': '采购订单预付款支付成功' if self.env.lang == 'zh_CN' else 'Purchase Order Advance Pay Success',
                        'date_deadline': fields.Date.today(),
                    })
                    self.order_state = '2'
        else:
            # 财务支付供应商预尾款
            if 'purchase_pay_state' in vals:
                if vals['purchase_pay_state']:
                    self.order_state = '6'
                    # 修改采购订单行当前为发货状态
                    purchase_order_lines = self.purchase_order_line_pay_ids.purchase_order_line_id
                    for line in purchase_order_lines:
                        line.current_state = '6'
                    # 删除支付预付款提醒
                    self.env['mail.activity'].sudo().search([
                        ('activity_type_id', '=', self.env['mail.activity.type'].search(
                            ['|', ('name', '=', '待办'), ('name', '=', 'To Do')]).id),
                        ('res_id', '=', self.id),
                        ('user_id', '=', self.env.user.id),
                        ('res_model_id', '=', self.env['ir.model']._get('purchase.order.pay.xks').id),
                        ('summary', '=', '您有一条待采购订单待支付' if self.env.lang == 'zh_CN' else 'Pending Purchase Order Pay')
                    ]).unlink()
                    # 创建预付款支付成功提醒
                    self.env['mail.activity'].sudo().create({
                        'res_model_id': self.env['ir.model']._get('purchase.order').id,
                        'res_id': self.purchase_order_id.id,
                        'user_id': 9,
                        'activity_type_id': self.env['mail.activity.type'].search(
                                ['|', ('name', '=', '待办'), ('name', '=', 'To Do')]).id,
                        'summary': '采购订单尾款款支付成功' if self.env.lang == 'zh_CN' else 'Purchase Order Balance Pay Success',
                        'date_deadline': fields.Date.today(),
                    })
                    # 修改商机状态为发货阶段
                    self.env['crm.lead'].search([('id', '=', self.purchase_order_id.opportunity_id.id)]).write({
                        'stage_id': 11,
                        'x_lead_status': '80',
                    })
        res = super().write(vals)
        return res


    # 提交采购预付款申请
    def apply_for_purchase_advance(self):
        self.order_state = '1'
        accountant_id = self.purchase_order_id.opportunity_id.accountant_id.id
        self.env['mail.activity'].sudo().create({
            'res_model_id': self.env['ir.model']._get('purchase.order.pay.xks').id,
            'res_id': self.id,
            'user_id': accountant_id,
            'activity_type_id': self.env['mail.activity.type'].search(['|', ('name', '=', '待办'), ('name', '=', 'To Do')]).id,
            'summary': '您有一条采购订单待支付' if self.env.lang == 'zh_CN' else 'Purchase Order Advance Pay',
            'date_deadline': fields.Date.today(),
        })

    # 通知销售告知客户付款
    def remind_customer_delivery(self):
        self.order_state = '3'
        self.env['mail.activity'].sudo().create({
            'res_model_id': self.env['ir.model']._get('crm.lead').id,
            'res_id': self.purchase_order_id.opportunity_id.id,
            'user_id': self.purchase_order_id.opportunity_id.user_id.id,
            'activity_type_id': self.env['mail.activity.type'].search(
                ['|', ('name', '=', '待办'), ('name', '=', 'To Do')]).id,
            'summary': '您有一个订单需要提醒客户支付发货款' if self.env.lang == 'zh_CN' else 'Remind Customer Delivery Pay',
            'date_deadline': fields.Date.today(),
        })

