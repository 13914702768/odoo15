# -*- coding: UTF-8 -*-
from odoo import api, fields, models

import logging
import datetime
import time

# Subset of partner fields: sync all or none to avoid mixed addresses
PARTNER_OTHER_FIELDS_TO_SYNC = [
    'x_level',
    'x_industry',
    'x_company_scale',
]

CUSTOMER_LEVEL = [
    ('1', 'A Class'),
    ('2', 'B Class'),
    ('3', 'C Class'),
    ('4', 'D Class'),
]

_logger = logging.getLogger(__name__)

class CrmLeadInheritXks(models.Model):
    _inherit = "crm.lead"
    
    # x_lead_status = fields.Selection([('0', '待申请商机'), ('1', '商机待审核'), ('2', '拒绝申请商机'), ('3', '同意申请商机')
    #                                   , ('4', '客户信息完善'), ('5', '确定需求'), ('6', '提供方案')
    #                                   , ('7', '报价中'), ('8', '报价待审核'), ('9', '同意报价'), ('10', '不同意报价')
    #                                   , ('15', '商务谈判')
    #                                   , ('20', '成交')
    #                                   , ('30', '待提交预付款审核'), ('31', '待确认预付款')
    #                                   # , ('40', '待采购'), ('41', '采购待审核'), ('42', '采购待支付')
    #                                   , ('50', '安排生产'), ('60', '验货')
    #                                   , ('70', '待提交发货款审核'), ('71', '待确认发货款')
    #                                   , ('80', '发货')
    #                                   , ('90', '待提交尾款审核'), ('91', '待确认尾款')], string='Current State'
    #                                   , default=lambda self: self.env.context.get('x_lead_status') or '0')
    x_lead_status = fields.Selection([('0', 'Business Opportunities to Apply for'), ('1', 'Opportunity pending review'),
                                      ('2', 'Reduse Opportunity'), ('3', 'Agree to apply for Business Opportunity'),
                                      ('4', 'Perfect Customer Information'), ('5', 'Requirement Determination'),
                                      ('6', 'Offer a Plan'), ('7', 'In the Quotation'), ('8', 'Audit Quotation'),
                                      ('9', 'Agree Quotation'), ('10', 'Disagree Quotation'),
                                      ('15', 'Business Negotiation'),
                                      ('20', 'Deal'), ('30', 'Request for Advance'), ('31', 'to be confirm Advance'),
                                      # ('40', '待采购'), ('41', '采购待审核'), ('42', '采购待支付')
                                      ('50', 'Arrange Production'), ('60', 'Examine Goods'),
                                      ('70', 'Submit Delivery Payment Review'), ('71', 'to be confirm Delivery Payment'),
                                      ('80', 'Ship'),
                                      ('90', 'Request for Balance'), ('91', 'to be confirm Balance')], string='Current State'
                                     , default=lambda self: self.env.context.get('x_lead_status') or '0')

    accountant_id = fields.Many2one('res.users', string='Financial Audit',
        domain="[('id', 'in', [11, 2])]",
        check_company=True, index=True, tracking=True)

    order_line = fields.One2many('crm.lead.order.line', 'lead_id', string='Order Lines', copy=True, auto_join=True)
    order_line_count = fields.Char(string='Order Lines Info')  #订单数量

    competitor = fields.One2many('crm.lead.competitor', 'lead_id', string='Competitor', copy=True, auto_join=True) # 竞争对手
    x_competitor_count = fields.Char(string='Competitor Info')  # 竞争对手数量

    x_level = fields.Selection(
        CUSTOMER_LEVEL, string='Level', index=True,
        default=CUSTOMER_LEVEL[0][0])

    x_industry = fields.Char('Industry', compute='_compute_partner_address_values', readonly=False, store=True) # 行业
    x_company_scale = fields.Char('Company Scale', compute='_compute_partner_address_values', readonly=False, store=True) # 公司规模

    x_current_sales_order_id = fields.Integer(string='Current Sales Order')   # 商机最终订单号
    x_current_sales_order_line = fields.One2many('sale.order.line', compute='_compute_sale_order_line_ids')
    note = fields.Html(string='Terms and conditions', compute='_compute_sale_order_line_ids')
    tax_totals_json = fields.Char(compute='_compute_sale_order_line_ids')
    advance_percentage = fields.Char(compute='_compute_sale_order_line_ids') # 预付款比例
    advance_total = fields.Char(string='Advance Amount', compute='_compute_sale_order_line_ids') # 预付款金额
    advance_pay_time = fields.Date(string='Advance Pay Time')
    x_advance_invoice = fields.Html(string='Advance Invoice') # 预付款单据

    middle_percentage = fields.Char(compute='_compute_sale_order_line_ids')
    middle_total = fields.Char(string='Delivery Amount', compute='_compute_sale_order_line_ids')
    middle_pay_time = fields.Date(string='Delivery Pay Time')
    x_middle_invoice = fields.Html(string='Delivery Invoice')  # 发货款单据

    balance_percentage = fields.Char(compute='_compute_sale_order_line_ids')
    balance_total = fields.Char(string='Balance Amount', compute='_compute_sale_order_line_ids')
    balance_pay_time = fields.Date(string='Balance Pay Time')
    x_balance_invoice = fields.Html(string='Balance Invoice') # 尾款单据

    x_contract_attachment_number = fields.Integer(compute='_compute_sale_order_line_ids', string='Number of Contract Attachments')

    x_pi_attachment_number = fields.Integer(compute='_compute_sale_order_line_ids', string='Number of PI Attachments')
    delivery_date = fields.Date(string='Contract Delivery Date')  # 合同交货期

    purchase_order_lines = fields.One2many('purchase.order', 'opportunity_id', string='Purchase Order', copy=True, auto_join=True)

    purchase_items = fields.One2many('purchase.order.line', string='Purchase Order Items',
                                           compute='_compute_purchase_items') #采购订单行

    purchase_items_inspection = fields.One2many('purchase.order.line', string='Purchase Order Items',
                                     compute='_compute_purchase_items')  # 采购订单行(验货)

    purchase_items_delivery_payment = fields.One2many('purchase.order.line', string='Purchase Order Items',
                                                compute='_compute_purchase_items')  # 采购订单行(发货款)
    
    leads_plan = fields.One2many('crm.lead.plan', 'lead_id', string='Leads plan', copy=True, auto_join=True)  # 线索方案
    x_plan_count = fields.Char(string='Plan Info')  # 线索方案数量



    def action_get_contract__attachment_view(self):
        """合同附件上传动作视图"""
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'sale.order'), ('res_id', '=', self.x_current_sales_order_id), ('description', '=', 'sale.order.contract')]
        res['context'] = {'default_res_model': 'sale.order', 'default_res_id': self.x_current_sales_order_id, 'default_description': 'sale.order.contract'}
        return res

    def action_get_pi__attachment_view(self):
        """PI附件上传动作视图"""
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'sale.order'), ('res_id', '=', self.x_current_sales_order_id),
                         ('description', '=', 'sale.order.pi')]
        res['context'] = {'default_res_model': 'sale.order', 'default_res_id': self.x_current_sales_order_id,
                          'default_description': 'sale.order.pi'}
        return res

    @api.depends('x_current_sales_order_id')
    def _compute_sale_order_line_ids(self):
        for lead in self:
            if lead.x_current_sales_order_id > 0:
                sales_order = self.env['sale.order'].search(
                    [('id', '=', lead.x_current_sales_order_id)])
                if sales_order:
                    self.x_current_sales_order_line = sales_order.order_line
                    self.note = sales_order.note
                    self.tax_totals_json = sales_order.tax_totals_json
                    self.advance_percentage = str(int(float(sales_order.advance_percentage) * 100)) + "%"
                    self.advance_total = sales_order.advance_total
                    self.middle_percentage = str(int(float(sales_order.middle_percentage) * 100)) + "%"
                    self.middle_total = sales_order.middle_total
                    self.balance_percentage = str(int(float(sales_order.balance_percentage) * 100)) + "%"
                    self.balance_total = sales_order.balance_total
                    self.x_contract_attachment_number = sales_order.x_contract_attachment_number
                    self.x_pi_attachment_number = sales_order.x_pi_attachment_number
            else:
                self.x_current_sales_order_line = None
                self.note = None
                self.tax_totals_json = None
                self.advance_percentage = None
                self.advance_total = None
                self.middle_percentage = None
                self.middle_total = None
                self.balance_percentage = None
                self.balance_total = None
                self.x_contract_attachment_number = None
                self.x_pi_attachment_number = None

    x_current_proposal = fields.Html(string='Current Proposal Description') # 现有方案描述
    x_customer_pain_points = fields.Html(string='Customer Pain Points') # 客户痛点
    x_hope_proposal = fields.Html(string='Hope Proposal Description')  # 期望方案描述

    #计算线索商机中客户预期采购多少种产品
    @api.onchange('order_line')
    def onchange_order_line(self):
        orders = self.order_line
        sale_orders = self.order_ids
        order_line_num = 0
        expected_revenue_xks = 0.00
        if len(sale_orders) > 0:
            if orders:
                for order in orders:
                    price = order.price_unit
                    buy_num = order.buy_number
                    order_line_num = order_line_num + 1
                self.order_line_count = str(order_line_num)
            else:
                self.order_line_count = None
        else:
            if orders:
                for order in orders:
                    price = order.price_unit
                    buy_num = order.buy_number
                    order_line_num = order_line_num + 1
                    expected_revenue_xks = expected_revenue_xks + price * buy_num
                self.order_line_count = str(order_line_num)
                self.expected_revenue = str(expected_revenue_xks)
            else:
                self.order_line_count = None
                if not self.x_plan_count:
                    self.expected_revenue = expected_revenue_xks
                else:
                    plans = self.leads_plan
                    for plan in plans:
                        expected_revenue_xks = expected_revenue_xks + plan.product_qty * plan.price_unit
                    self.expected_revenue = str(expected_revenue_xks)

    @api.onchange('competitor')
    def onchange_competitor(self):
        competitors = self.competitor
        competitor_num = 0
        if competitors:
            for competitor in competitors:
                competitor_num = competitor_num + 1
            self.x_competitor_count = str(competitor_num)
        else:
            self.x_competitor_count = None
    
    @api.onchange('leads_plan')
    def onchange_leads_plan(self):
        expected_revenue_xks = 0.00
        leads_plan = self.leads_plan
        orders = self.order_line
        leads_plan_num = 0
        if leads_plan:
            for plan in leads_plan:
                if orders:
                    for order in orders:
                        price = order.price_unit
                        buy_num = order.buy_number
                        expected_revenue_xks = expected_revenue_xks + price * buy_num
                else:
                    expected_revenue_xks = expected_revenue_xks + plan.product_qty * plan.price_unit
                leads_plan_num = leads_plan_num + 1
            self.x_plan_count = str(leads_plan_num)
            self.expected_revenue = str(expected_revenue_xks)
        else:
            self.x_plan_count = None
            if orders:
                for order in orders:
                    price = order.price_unit
                    buy_num = order.buy_number
                    expected_revenue_xks = expected_revenue_xks + price * buy_num
            self.expected_revenue = str(expected_revenue_xks)

    # 控制新的报价单按钮跳转报价页面后发送邮件和报价申请按钮显示隐藏
    def action_new_quotation(self):
        action = self.env["ir.actions.actions"]._for_xml_id("sale_crm.sale_action_quotations_new")
        lead_status = self.x_lead_status
        default_x_lead_status = 0
        default_quote_request = 1
        default_audit_but = 1
        if lead_status == '7' or lead_status == '8' or lead_status == '10':
            default_x_lead_status = 1  #发送邮件按钮不可见
            if lead_status == '7' or lead_status == '10':
                default_quote_request = 0  #报价申请按钮可见
            if lead_status == '8':
                default_audit_but = 0  #报价审核按钮可见

        action['context'] = {
            'search_default_opportunity_id': self.id,
            'default_opportunity_id': self.id,
            'default_x_lead_status': default_x_lead_status,
            'default_quote_request': default_quote_request,
            'default_audit_but': default_audit_but,
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_campaign_id': self.campaign_id.id,
            'default_medium_id': self.medium_id.id,
            'default_origin': self.name,
            'default_source_id': self.source_id.id,
            'default_company_id': self.company_id.id or self.env.company.id,
            'default_tag_ids': [(6, 0, self.tag_ids.ids)]
        }
        if self.team_id:
            action['context']['default_team_id'] = self.team_id.id,
        if self.user_id:
            action['context']['default_user_id'] = self.user_id.id
        return action

    # 控制报价单列表(单条报价)跳转报价页面后发送邮件和报价申请按钮显示隐藏
    def action_view_sale_quotation(self):
        lead_status = self.x_lead_status
        default_x_lead_status = 0
        default_quote_request = 1
        default_audit_but = 1
        if lead_status == '7' or lead_status == '8' or lead_status == '10':
            default_x_lead_status = 1  # 发送邮件按钮不可见
            if lead_status == '7' or lead_status == '10':
                default_quote_request = 0  # 报价申请按钮可见
            if lead_status == '8':
                default_audit_but = 0  # 报价审核按钮可见
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_quotations_with_onboarding")
        action['context'] = {
            'search_default_draft': 1,
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_opportunity_id': self.id,
            'default_x_lead_status': default_x_lead_status,
            'default_quote_request': default_quote_request,
            'default_audit_but': default_audit_but,
        }
        action['domain'] = [('opportunity_id', '=', self.id), ('state', 'in', ['draft', 'sent'])]
        quotations = self.mapped('order_ids').filtered(lambda l: l.state in ('draft', 'sent'))
        if len(quotations) == 1:
            action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
            action['res_id'] = quotations.id
        return action

    # 同意线索申请
    def agree_to_lead_application_xks(self):
        print("同意线索转商机申请")
        model_id = self.env['ir.model']._get(self._name).id
        activity_type = self.env['mail.activity.type'].search(['|', ('name', '=', '待办'), ('name', '=', 'To Do')])
        for lead in self.ids:
            self.env['crm.lead'].search([('id', '=', lead)]).write({
                'x_lead_status': '4',
                'state_id': 1,
                'probability': 10,
            })
            # 删除线索转商机审核提醒
            self.env['mail.activity'].sudo().search([
                ('activity_type_id', '=', activity_type.id),
                ('res_id', '=', lead),
                ('user_id', '=', self.env.user.id),
                ('res_model_id', '=', model_id)
            ]).unlink()
        # 刷新当前页面
        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }

    #拒绝线索申请
    def reject_lead_application_xks(self):
        print("拒绝线索转商机申请")
        model_id = self.env['ir.model']._get(self._name).id
        activity_type = self.env['mail.activity.type'].search(['|', ('name', '=', '待办'), ('name', '=', 'To Do')])
        for lead in self.ids:
            self.env['crm.lead'].search([('id', '=', lead)]).write({
                'x_lead_status': '2',
                'type': 'lead',
            })
            # 删除线索转商机审核提醒
            self.env['mail.activity'].sudo().search([
                ('activity_type_id', '=', activity_type.id),
                ('res_id', '=', lead),
                ('user_id', '=', self.env.user.id),
                ('res_model_id', '=', model_id)
            ]).unlink()

    # 跳转确定需求阶段
    def go_to_identify_needs_xks(self):
        print("进入确定需求阶段")
        for lead in self.ids:
            if not self.partner_id:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': '提示',
                        'message': '客户名称不能为空' if self.env.lang == 'zh_CN' else 'Customer name cannot be empty',
                        'sticky': False,  # 手动关闭   False 延时关闭
                        'className': 'bg-danger',  # 背景颜色  bg-success   bg-warning  bg-info
                    }
                }
            else:
                res = self.env['crm.lead'].search([('id', '=', lead)])
                res.write({
                    'stage_id': 2,
                    'x_lead_status': '5',
                    'probability': 20,
                })

    # 跳转提供方案阶段
    def go_to_provide_plan_xks(self):
        print("进入提供方案阶段")
        for lead in self.ids:
            res = self.env['crm.lead'].search([('id', '=', lead)]).write({
                'stage_id': 3,
                'x_lead_status': '6',
                'probability': 25,
            })

    # 跳转提供报价阶段
    def go_to_provide_pricing_xks(self):
        print("进入提供报价阶段")
        for lead in self.ids:
            if not self.order_line_count:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': '提示',
                        'message': '项目方案不能为空' if self.env.lang == 'zh_CN' else 'Project Proposals cannot be empty',
                        'sticky': False,  # 手动关闭   False 延时关闭
                        'className': 'bg-danger',  # 背景颜色  bg-success   bg-warning  bg-info
                    }
                }
            else:
                 self.env['crm.lead'].search([('id', '=', lead)]).write({
                    'stage_id': 4,
                    'x_lead_status': '7',
                    'probability': 30,
                 })

    # 跳转商务谈判阶段
    def go_to_negotiation_xks(self):
        print("进入商务谈判阶段")
        for lead in self.ids:
            res = self.env['crm.lead'].search([('id', '=', lead)]).write({
                'stage_id': 5,
                'x_lead_status': '15',
                'probability': 50,
            })

    # 进入成交阶段
    def go_to_deal_xks(self):
        for lead in self.ids:
            orders = self.env['sale.order'].search([('opportunity_id', '=', lead)]).sorted('id')
            orderid = 0
            for order in orders:
                if order.id > orderid:
                    orderid = order.id
            current_order = self.env['sale.order'].search([('id', '=', orderid)])
            total_price = 0
            for line in current_order.order_line:
                total_price = total_price + line.price_total
            res = self.env['crm.lead'].search([('id', '=', lead)]).write({
                'stage_id': 6,
                'x_lead_status': '20',
                'x_current_sales_order_id': str(orderid),
                'probability': 80,
                'expected_revenue': total_price,
            })

    # 进入预付款阶段
    def go_to_prepayment_review_xks(self):
        print("进入预付款阶段")
        for lead in self.ids:
            if self.x_contract_attachment_number == 0:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': '提示',
                        'message': '合同附件必传' if self.env.lang == 'zh_CN' else 'Contract attachments must be upload',
                        'sticky': False,  # 手动关闭   False 延时关闭
                        'className': 'bg-danger',  # 背景颜色  bg-success   bg-warning  bg-info
                    }
                }
            if self.x_pi_attachment_number == 0:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': '提示',
                        'message': 'PI附件必传' if self.env.lang == 'zh_CN' else 'PI attachments must be upload',
                        'sticky': False,  # 手动关闭   False 延时关闭
                        'className': 'bg-danger',  # 背景颜色  bg-success   bg-warning  bg-info
                    }
                }
            res = self.env['crm.lead'].search([('id', '=', lead)]).write({
                'stage_id': 7,
                'x_lead_status': '30',
                'probability': 90,
            })

    # 提交预付款审核
    def prepayment_review_xks(self):
        print("提交预付款审核")
        for lead in self:
            if lead.accountant_id:
                model_id = self.env['ir.model']._get(self._name).id
                activity_type = self.env['mail.activity.type'].search(['|', ('name', '=', '待办'), ('name', '=', 'To Do')])
                self.env['mail.activity'].sudo().create({
                    'res_model_id': model_id,
                    'res_id': lead.id,
                    'user_id': self.accountant_id.id,
                    'activity_type_id': activity_type.id,
                    'summary': '预付款审核' if self.env.lang == 'zh_CN' else 'Advance Audit',
                    'date_deadline': fields.Date.today(),
                })
                res = self.env['crm.lead'].search([('id', '=', lead.id)]).write({
                    'stage_id': 7,
                    'x_lead_status': '31',
                })
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': '提示',
                        'message': '财务审核人不能为空' if self.env.lang == 'zh_CN' else 'Financial auditor cannot be empty',
                        'sticky': False,  # 手动关闭   False 延时关闭
                        'className': 'bg-danger',  # 背景颜色  bg-success   bg-warning  bg-info
                    }
                }

    # 财务确认预付款
    def prepayment_review_audit_xks(self):
        print("预付款确认")
        model_id = self.env['ir.model']._get(self._name).id
        activity_type = self.env['mail.activity.type'].search(['|', ('name', '=', '待办'), ('name', '=', 'To Do')])
        for lead in self.ids:
            res = self.env['crm.lead'].search([('id', '=', lead)]).write({
                'stage_id': 8,
                'x_lead_status': '50',
                'probability': 100,
            })
            # 删除线索转商机审核提醒
            self.env['mail.activity'].sudo().search([
                ('activity_type_id', '=', activity_type.id),
                ('res_id', '=', lead),
                ('user_id', '=', self.env.user.id),
                ('res_model_id', '=', model_id)
            ]).unlink()
            #创建采购订单
            purchase = self.env['purchase.order'].create({
                'opportunity_id': lead,
                'name': self.env['ir.sequence'].next_by_code('purchase.order', sequence_date=None) or '/',
                'priority': '0',
                'date_order': fields.Date.today(),
                'partner_id': 26,
                'currency_id': 7,
                'state': 'draft',
                'invoice_count': 0,
                'invoice_status': 'no',
                'user_id': self.env.user.id,
                'company_id': 1,
                'currency_rate': 1,
                'mail_reminder_confirmed': False,
                'mail_reception_confirmed': False,
            })
            # #通知采购
            self.env['mail.activity'].sudo().create({
                'res_model_id': self.env['ir.model']._get('purchase.order').id,
                'res_id': purchase.id,
                'user_id': 9,
                'activity_type_id': activity_type.id,
                'summary': '您有一条待采购订单需要处理' if self.env.lang == 'zh_CN' else 'Pending Purchase Order Processing',
                'date_deadline': fields.Date.today(),
            })
        # 刷新当前页面
        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }

    # 提交发货款审核
    def submit_delivery_payment_review_xks(self):
        print("提交发货款审核")
        for lead in self:
            if lead.accountant_id:
                self.env['mail.activity'].sudo().create({
                    'res_model_id': self.env['ir.model']._get(self._name).id,
                    'res_id': lead.id,
                    'user_id': lead.accountant_id.id,
                    'activity_type_id': self.env['mail.activity.type'].search(['|', ('name', '=', '待办'), ('name', '=', 'To Do')]).id,
                    'summary': '有发货款待审核' if self.env.lang == 'zh_CN' else 'Delivery Payment Review',
                    'date_deadline': fields.Date.today(),
                })
                res = self.env['crm.lead'].search([('id', '=', lead.id)]).write({
                    'stage_id': 10,
                    'x_lead_status': '71',
                })
                purchase_order_pays = self.env['purchase.order.pay.xks'].search([
                    ('purchase_order_id.opportunity_id', '=', lead.id),
                    ('pay_project', '=', '2'),
                    ('order_state', '=', '3')
                ])
                if len(purchase_order_pays) > 0:
                   purchase_order_pays[0].write({'order_state':'4'})
                # 删除客户发货款提醒
                self.env['mail.activity'].sudo().search([
                    ('activity_type_id', '=', self.env['mail.activity.type'].search(
                        ['|', ('name', '=', '待办'), ('name', '=', 'To Do')]).id),
                    ('res_id', '=', lead.id),
                    ('user_id', '=', self.env.user.id),
                    ('res_model_id', '=', self.env['ir.model']._get('crm.lead').id),
                    ('summary', '=', '您有一个订单需要提醒客户支付发货款' if self.env.lang == 'zh_CN' else 'Remind Customer Delivery Pay')
                ]).unlink()
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': '提示',
                        'message': '财务审核人不能为空' if self.env.lang == 'zh_CN' else 'Financial auditor cannot be empty',
                        'sticky': False,  # 手动关闭   False 延时关闭
                        'className': 'bg-danger',  # 背景颜色  bg-success   bg-warning  bg-info
                    }
                }

    # 财务发货款审核
    def delivery_payment_audit_xks(self):
        print("发货款确认")
        model_id = self.env['ir.model']._get(self._name).id
        activity_type = self.env['mail.activity.type'].search(['|', ('name', '=', '待办'), ('name', '=', 'To Do')])
        for lead in self:
            res = self.env['crm.lead'].search([('id', '=', lead.id)]).write({
                'stage_id': 11,
                'x_lead_status': '80',
            })
            # 删除发货款审核提醒
            self.env['mail.activity'].sudo().search([
                ('activity_type_id', '=', activity_type.id),
                ('res_id', '=', lead.id),
                ('user_id', '=', self.env.user.id),
                ('res_model_id', '=', model_id),
                ('summary', '=', '有发货款待审核' if self.env.lang == 'zh_CN' else 'Delivery Payment Review')
            ]).unlink()
            purchase_order_pays = self.env['purchase.order.pay.xks'].search([
                    ('purchase_order_id.opportunity_id', '=', self.id),
                    ('pay_project', '=', '2'),
                    ('order_state', '=', '4')
                ])
            if len(purchase_order_pays) > 0:
                purchase_order_pays[0].write({'order_state': '5', 'customer_pay_state': True})
                accountant_id = purchase_order_pays[0].purchase_order_id.opportunity_id.accountant_id.id
                self.env['mail.activity'].sudo().create({
                    'res_model_id': self.env['ir.model']._get('purchase.order.pay.xks').id,
                    'res_id': purchase_order_pays[0].id,
                    'user_id': accountant_id,
                    'activity_type_id': activity_type.id,
                    'summary': '您有一条待采购订单待支付' if self.env.lang == 'zh_CN' else 'Pending Purchase Order Pay',
                    'date_deadline': fields.Date.today(),
                })
        # 刷新当前页面
        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }

    # 跳转尾款阶段
    def go_to_balance_stage(self):
        print("进入尾款阶段")
        for lead in self.ids:
            res = self.env['crm.lead'].search([('id', '=', lead)]).write({
                'stage_id': 12,
                'x_lead_status': '90',
            })

    # 提交尾款审核
    def submit_banace_payment_review_xks(self):
        print("提交发货款审核")
        for lead in self:
            if self.accountant_id:
                self.env['mail.activity'].sudo().create({
                    'res_model_id': self.env['ir.model']._get(self._name).id,
                    'res_id': lead.id,
                    'user_id': 8,
                    'activity_type_id': self.env['mail.activity.type'].search(['|', ('name', '=', '待办'), ('name', '=', 'To Do')]).id,
                    'summary': '有尾款待审核' if self.env.lang == 'zh_CN' else 'Balance Review',
                    'date_deadline': fields.Date.today(),
                })
                self.env['crm.lead'].search([('id', '=', lead.id)]).write({
                    'x_lead_status': '91',
                })
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': '提示',
                        'message': '财务审核人不能为空' if self.env.lang == 'zh_CN' else 'Financial auditor cannot be empty',
                        'sticky': False,  # 手动关闭   False 延时关闭
                        'className': 'bg-danger',  # 背景颜色  bg-success   bg-warning  bg-info
                    }
                }

    # 财务确认尾款
    def balance_prepayment_audit_xks(self):
        print("尾款确认")
        model_id = self.env['ir.model']._get(self._name).id
        activity_type = self.env['mail.activity.type'].search(['|', ('name', '=', '待办'), ('name', '=', 'To Do')])
        for lead in self:
            res = self.env['crm.lead'].search([('id', '=', lead.id)]).write({
                'x_lead_status': '92',
            })
            # 删除尾款审核审核提醒
            self.env['mail.activity'].sudo().search([
                ('activity_type_id', '=', activity_type.id),
                ('res_id', '=', lead.id),
                ('user_id', '=', self.env.user.id),
                ('res_model_id', '=', model_id),
                ('summary', '=', '有尾款待审核' if self.env.lang == 'zh_CN' else 'Balance Review')
            ]).unlink()
        # 刷新当前页面
        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }

    #发送线索转商机提醒
    # @api.onchange('x_lead_status')
    def create_review_leads_xks_activity(self):
        status = self.x_lead_status
        for lead in self.ids:
            if status == '1':
                model_id = self.env['ir.model']._get(self._name).id
                activity_type = self.env['mail.activity.type'].search(['|', ('name', '=', '待办'), ('name', '=', 'To Do')])
                self.env['mail.activity'].sudo().create({
                    'res_model_id': model_id,
                    'res_id': lead,
                    'user_id': 6,
                    'activity_type_id': activity_type.id,
                    'summary': '有待审核的线索申请',
                    'date_deadline': fields.Date.today(),
                })

    #打开视图
    def open_leads_form(self):
        print('打开商机线索页面',self.id)
        form_id = self.env.ref('crm.crm_lead_view_form').id
        return {
            'view_type': 'form',
            'view_mode': 'form',  # 打开form视图
            'res_model': 'crm.lead',  # 打开模型
            'type': 'ir.actions.act_window',  # 窗口动作
            'res_id': self.id,
            'views': [[form_id, 'form']],
            'context': {
                'type': 'lead',
                'create': False,
                'active_test': False,
            },
            'target': 'current', # new打开新页面
            'flags': {'initial_mode': 'view', 'action_buttons': False},
        }

    def convert_opportunity_xks(self, partner_id, user_ids=False, team_id=False):
        customer = False
        if partner_id:
            customer = self.env['res.partner'].browse(partner_id)
        for lead in self:
            if not lead.active or lead.probability == 100:
                continue
            vals = lead._convert_opportunity_data(customer, team_id)
            if lead.user_id is not None and lead.user_id.id == self.env.uid:
                # 自己线索无需审核
                vals['x_lead_status'] = "4"
            else:
                # 发送线索转商机申请审核提醒
                if self.x_lead_status == '0':
                    model_id = self.env['ir.model']._get(self._name).id
                    activity_type = self.env['mail.activity.type'].search(
                        ['|', ('name', '=', '待办'), ('name', '=', 'To Do')])
                    self.env['mail.activity'].sudo().create({
                        'res_model_id': model_id,
                        'res_id': lead,
                        'user_id': 6,
                        'activity_type_id': activity_type.id,
                        'summary': '有待审核的线索申请',
                        'date_deadline': fields.Date.today(),
                    })
                vals['x_lead_status'] = "1"
            # 默认date_deadline时间为3个月后
            date_deadline = (datetime.datetime.now() + datetime.timedelta(days=90)).strftime("%Y-%m-%d")
            vals['date_deadline'] = date_deadline
            lead.write(vals)
        if user_ids or team_id:
            self._handle_salesmen_assignment(user_ids=user_ids, team_id=team_id)

        return True

    @api.depends('partner_id')
    def _compute_partner_address_values(self):
        """ Sync all or none of address fields """
        for lead in self:
            lead.update(lead._prepare_address_values_from_partner(lead.partner_id))
            lead.update(lead._prepare_other_values_from_partner(lead.partner_id))

    def _prepare_other_values_from_partner(self, partner):
        # Sync all other fields from partner, or none, to avoid mixing them.
        if any(partner[f] for f in PARTNER_OTHER_FIELDS_TO_SYNC):
            values = {f: partner[f] for f in PARTNER_OTHER_FIELDS_TO_SYNC}
        else:
            values = {f: self[f] for f in PARTNER_OTHER_FIELDS_TO_SYNC}
        return values

    @api.depends('purchase_order_lines')
    def _compute_purchase_items(self):
        for lead in self:
            lead.purchase_items = None
            lead.purchase_items_inspection = None
            lead.purchase_items_delivery_payment = None
            if len(lead.purchase_order_lines.ids) > 0:
                order_items = self.env['purchase.order.line'].search([('order_id', 'in', lead.purchase_order_lines.ids)])
                order_items_inspection = self.env['purchase.order.line'].search([
                    ('order_id', 'in', lead.purchase_order_lines.ids),
                    ('current_state', '=', '4')
                ])
                order_items_delivery_payment = self.env['purchase.order.line'].search([
                    ('order_id', 'in', lead.purchase_order_lines.ids),
                    ('current_state', '=', '5')
                ])
                if order_items:
                    lead.purchase_items = order_items
                    lead.purchase_items_inspection = order_items_inspection
                    lead.purchase_items_delivery_payment = order_items_delivery_payment







