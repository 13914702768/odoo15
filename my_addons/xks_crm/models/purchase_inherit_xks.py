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

PURCHASE_ORDER_LINE_STATE = [
    ('1', '确定生产订单'),
    ('2', '预付款'),
    ('3', '生产中'),
    ('4', '验货'),
    ('5', '尾款'),
    ('6', '发货'),
    ('7', '到达起运港'),
    ('8', '离开起运港'),
    ('9', '到达目的地港'),
]

PRODUCE_STATE = [
    ('1', '铸件，床身'),
    ('2', '电气，油路，气路等装配'),
    ('3', '制作夹具'),
    ('4', '工厂调试'),
    ('5', '生产完成'),
]
class PurchaseInheritXks(models.Model):
    _inherit = "purchase.order"

    opportunity_id = fields.Many2one('crm.lead', string='Opportunity',
                                     # domain = "[('x_lead_status', '=', '40')]",
                                     ondelete='cascade', index=True, copy=False)

    opportunity_order_lines = fields.One2many('sale.order.line', compute='_compute_sale_order_line_ids')

    purchase_contract_attachment_number = fields.Integer(compute='_compute_purchase_contract_attachment_number',
                                                 string='Number of Purchase Contract Attachments')


    @api.depends('opportunity_id')
    def _compute_sale_order_line_ids(self):
        for order in self:
            if len(order.opportunity_id.ids) > 0:
                sales_order = self.env['sale.order'].search(
                    [('id', '=', order.opportunity_id.x_current_sales_order_id)])
                if sales_order:
                    self.opportunity_order_lines = sales_order.order_line
            else:
                self.opportunity_order_lines = None

    def write(self, vals):
        vals, partner_vals = self._write_partner_values(vals)
        if 'state' in vals:
            if vals['state'] != 'draft':
                # 删除采购订单提醒
                reminder = self.env['mail.activity'].sudo().search([
                    ('activity_type_id', '=',
                     self.env['mail.activity.type'].search(['|', ('name', '=', '待办'), ('name', '=', 'To Do')]).id),
                    ('res_id', '=', self.id),
                    ('summary', '=', '您有一条待采购订单需要处理' if self.env.lang == 'zh_CN' else 'Pending Purchase Order Processing'),
                    ('user_id', '=', self.env.user.id),
                    ('res_model_id', '=', self.env['ir.model']._get('purchase.order').id)
                ]).unlink()
        res = super().write(vals)
        if partner_vals:
            self.partner_id.sudo().write(partner_vals)  # Because the purchase user doesn't have write on `res.partner`
        return res

    def _compute_purchase_contract_attachment_number(self):
        """采购合同上传"""
        attachment_data = self.env['ir.attachment'].read_group(
            [('res_model', '=', 'purchase.order'), ('res_id', 'in', self.ids), ('description', '=', 'purchase.order.contract')], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for expense in self:
            expense.purchase_contract_attachment_number = attachment.get(expense.id, 0)

    def action_get_purchase_contract_attachment_view(self):
        """采购合同附件上传动作视图"""
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'purchase.order'), ('res_id', 'in', self.ids), ('description', '=', 'purchase.order.contract')]
        res['context'] = {'default_res_model': 'purchase.order', 'default_res_id': self.id, 'default_description': 'purchase.order.contract'}
        return res

    @api.depends('advance_percentage', 'balance_percentage')
    def _amount_by_percentage(self):
        for order in self:
            if order.advance_percentage:
                order.advance_total = float(order.amount_total) * float(order.advance_percentage)
            else:
                order.advance_total = None
            if order.balance_percentage:
                order.balance_total = float(order.amount_total) * float(order.balance_percentage)
            else:
                order.balance_total = None

    def _compute_x_advance_attachment_number(self):
        """预付款附件上传"""
        attachment_data = self.env['ir.attachment'].read_group(
            [('res_model', '=', 'purchase.order'), ('res_id', 'in', self.ids), ('description', '=', 'purchase.order.advance')], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for expense in self:
            expense.x_advance_attachment_number = attachment.get(expense.id, 0)

    def action_get_advance__attachment_view(self):
        """预付款附件上传动作视图"""
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'purchase.order'), ('res_id', 'in', self.ids), ('description', '=', 'purchase.order.advance')]
        res['context'] = {'default_res_model': 'purchase.order', 'default_res_id': self.id, 'default_description': 'purchase.order.advance'}
        return res

    def _compute_x_balance_attachment_number(self):
        """尾款附件上传"""
        attachment_data = self.env['ir.attachment'].read_group(
            [('res_model', '=', 'purchase.order'), ('res_id', 'in', self.ids), ('description', '=', 'purchase.order.balance')], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for expense in self:
            expense.x_balance_attachment_number = attachment.get(expense.id, 0)

    def action_get_balance_attachment_view(self):
        """尾款附件上传动作视图"""
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'purchase.order'), ('res_id', 'in', self.ids), ('description', '=', 'purchase.order.balance')]
        res['context'] = {'default_res_model': 'purchase.order', 'default_res_id': self.id, 'default_description': 'purchase.order.balance'}
        return res

    # 订单确认
    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order._approval_allowed():
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
            order_lines = order.order_line
            for order_line in order_lines:
                order_line.current_state = '2'
        return True

    def open_purchase_order_pay_list(self):
         return {
            'name': '采购订单支付' if self.env.lang == 'zh_CN' else 'Purchase Order Pay',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'purchase.order.pay.xks',
            'context': dict(
                self.env.context,
                purchase_order_id=self.id
            ),
            'domain': [('purchase_order_id', '=', self.id)],
            'target': 'current',  # new打开新页面    current当前页面
         }



class PurchaseOrderLineInheritXks(models.Model):
    _inherit = "purchase.order.line"

    product_template_id = fields.Many2one(
        'product.template', string='Product Template',
        related="product_id.product_tmpl_id")

    current_state = fields.Selection(PURCHASE_ORDER_LINE_STATE, string='Current State', index=True, default=PURCHASE_ORDER_LINE_STATE[0][0])
    produce_ids = fields.One2many('product.produce.xks', 'purchase_order_line_id', string='Produce State', copy=True, auto_join=True)  # 生产状态
    inspection_ids = fields.One2many('product.inspection.xks', 'purchase_order_line_id', string='Inspection', copy=True, auto_join=True)  # 验货

    delivery_qty = fields.Float(string="Delivery Unpaid Quantity", compute='_compute_delivery_items')  # 发货数量
    delivery_price = fields.Float(string="Delivery Unpaid Price", compute='_compute_delivery_items')   # 发货金额（支付工厂）
    customer_delivery_price = fields.Float(string="Customer Delivery Unpaid Price", compute='_compute_delivery_items') # 发货金额（客户支付发货款）

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

    @api.model
    def create(self, vals):
        vals['current_state'] = '1'
        res = super().create(vals)
        return res

    # 打开生产列表视图
    def open_product_produce_list(self):
         return {
            'name': '生产状态' if self.env.lang == 'zh_CN' else 'Produce State',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'product.produce.xks',
            'context': dict(
                self.env.context,
                purchase_order_line_id=self.id
            ),
            'domain': [('purchase_order_line_id', '=', self.id)],
            'target': 'current',  # new打开新页面    current当前页面
         }

    # 打开验货列表视图
    def open_product_inspection_list(self):
         return {
            'name': '验货' if self.env.lang == 'zh_CN' else 'Inspection',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'product.inspection.xks',
            'context': dict(
                self.env.context,
                purchase_order_line_id=self.id
            ),
            'domain': [('purchase_order_line_id', '=', self.id)],
            'target': 'current',  # new打开新页面    current当前页面
         }

    # 打开发货视图
    def open_product_ship_list(self):
        # 修改商机为尾款阶段
        self.env['crm.lead'].search([('id', '=', self.order_id.opportunity_id.id)]).write({
            'stage_id': 11,
            'x_lead_status': '80',
        })
        # 删除采购尾款支付成功提醒
        self.env['mail.activity'].sudo().search([
            ('activity_type_id', '=', self.env['mail.activity.type'].search(
                ['|', ('name', '=', '待办'), ('name', '=', 'To Do')]).id),
            ('res_id', '=', self.order_id.id),
            ('user_id', '=', self.env.user.id),
            ('res_model_id', '=', self.env['ir.model']._get('purchase.order').id),
            ('summary', '=', '采购订单尾款款支付成功' if self.env.lang == 'zh_CN' else 'Purchase Order Balance Pay Success')
        ]).unlink()

    def confirm_advance_pay(self):
        order_current_state = self.current_state
        if order_current_state == '2':
            self.current_state = '3'

    def confirm_balance_pay(self):
        order_current_state = self.current_state
        if order_current_state == '4':
            self.current_state = '5'

    # 计算销售订单未支付的数量和金额
    def _compute_delivery_items(self):
        for line in self:
            deliverys = self.env['purchase.order.line.pay.xks'].search([
                                ('purchase_order_line_id', '=', line.id)
                        ])
            sales_order_id = line.order_id.opportunity_id.x_current_sales_order_id
            sales_order = self.env['sale.order'].search([('id', '=', sales_order_id)])
            c_product_id = self.product_id
            sales_order_lines = self.env['sale.order.line'].search([('product_id', '=', c_product_id.id),
                                                                    ('order_id', '=', sales_order.id)])
            need_qty = 0.0
            payment_qty = 0.0
            for delivery in deliverys:
                # 尾款
                if delivery.purchase_order_pay_id.pay_project == '2':
                    # 客户支付状态为已支付
                    if delivery.purchase_order_pay_id.customer_pay_state:
                        payment_qty = payment_qty + delivery.payment_qty
                    else:
                        need_qty = need_qty + delivery.payment_qty
            if payment_qty > line.product_qty:
                payment_qty = line.product_qty
            if need_qty > line.product_qty:
                need_qty = line.product_qty
            line.delivery_qty = need_qty
            line.delivery_price = need_qty * line.price_unit
            if len(sales_order_lines) > 0:
                sales_order_line = sales_order_lines[0]
            line.customer_delivery_price = need_qty * sales_order_line.price_unit * float(sales_order.middle_percentage)









