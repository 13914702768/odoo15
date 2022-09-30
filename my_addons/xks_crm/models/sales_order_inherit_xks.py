# -*- coding: utf-8 -*-
from  odoo import api, fields, models


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

class SalesOrderInheritXks(models.Model):
    _inherit = 'sale.order'

    # x_audit_status = fields.Char(string='审核状态', default='0')  # 0、无需审核  1、待审核  2、审核通过  3、审核不通过

    leads_order_line_ids = fields.Many2many(
        'crm.lead.order.line', compute='_compute_leads_order_line_ids')

    advance_percentage = fields.Selection(
        PAYMENT_PERCENTAGE, string='Advance Percentage', index=True)
    advance_total = fields.Monetary(string='Advance Amount', store=True, compute='_amount_by_percentage', tracking=4)

    middle_percentage = fields.Selection(
        PAYMENT_PERCENTAGE, string='Middle Percentage', index=True) # ,default=PAYMENT_PERCENTAGE[6][0]
    middle_total = fields.Monetary(string='Middle Amount', store=True, compute='_amount_by_percentage', tracking=4)

    balance_percentage = fields.Selection(PAYMENT_PERCENTAGE, string='Balance Percentage', index=True)
    balance_total = fields.Monetary(string='Balance Amount', store=True, compute='_amount_by_percentage', tracking=4)

    delivery_date = fields.Date(string='Contract Delivery Date', index=True) # 合同交货期

    x_contract_attachment_number = fields.Integer(compute='_compute_x_contract_attachment_number', string='Number of Contract Attachments')
    x_pi_attachment_number = fields.Integer(compute='_compute_x_pi_attachment_number', string='Number of PI Attachments')

    audit_state = fields.Char(string="Audit State", default='defaul', tracking=True) #报价申请审核状态   defaul未申请审核  audit待审核   agree同意   reject驳回
    @api.onchange('advance_percentage', 'middle_percentage')
    def _get_balance_percentage(self):
        advance = self.advance_percentage
        middle = self.middle_percentage
        total = 0.0
        if advance:
            total = total + float(advance)
        if middle:
            total = total + float(middle)
        print(total)
        index = 10 - int(total*10) - 1
        if index < 0:
            index = 0

        self.balance_percentage = PAYMENT_PERCENTAGE[index][0]

    def _compute_x_contract_attachment_number(self):
        """合同附件上传"""
        attachment_data = self.env['ir.attachment'].read_group(
            [('res_model', '=', self._name), ('res_id', 'in', self.ids), ('description', '=', 'sale.order.contract')], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for expense in self:
            expense.x_contract_attachment_number = attachment.get(expense.id, 0)

    def action_get_contract__attachment_view(self):
        """合同附件上传动作视图"""
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', self._name), ('res_id', 'in', self.ids), ('description', '=', 'sale.order.contract')]
        res['context'] = {'default_res_model': self._name, 'default_res_id': self.id, 'default_description': 'sale.order.contract'}
        return res

    def _compute_x_pi_attachment_number(self):
        """PI附件上传"""
        attachment_data = self.env['ir.attachment'].read_group(
            [('res_model', '=', self._name), ('res_id', 'in', self.ids), ('description', '=', 'sale.order.pi')],
            ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for expense in self:
            expense.x_pi_attachment_number = attachment.get(expense.id, 0)

    def action_get_pi__attachment_view(self):
        """PI附件上传动作视图"""
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', self._name), ('res_id', 'in', self.ids),
                         ('description', '=', 'sale.order.pi')]
        res['context'] = {'default_res_model': self._name, 'default_res_id': self.id,
                          'default_description': 'sale.order.pi'}
        return res

    @api.depends('opportunity_id')
    def _compute_leads_order_line_ids(self):
        for order in self:
            leads_order_line = self.env['crm.lead.order.line'].search([('lead_id.id', '=', order.opportunity_id.id)])
            self.leads_order_line_ids = leads_order_line


    @api.depends('advance_percentage', 'middle_percentage', 'balance_percentage')
    def _amount_by_percentage(self):
        for order in self:
            if order.advance_percentage:
                order.advance_total = float(order.amount_total) * float(order.advance_percentage)
            else:
                order.advance_total = None
            if order.middle_percentage:
                order.middle_total = float(order.amount_total) * float(order.middle_percentage)
            else:
                order.middle_total = None
            if order.balance_percentage:
                order.balance_total = float(order.amount_total) * float(order.balance_percentage)
            else:
                order.balance_total = None

    # 发送报价审核申请
    def create_quote_request_xks_activity(self):
        opportunityid = self.opportunity_id
        for order in self:
            model_id = self.env['ir.model']._get(self._name).id
            activity_type = self.env['mail.activity.type'].search([('name', '=', 'reminder')])
            self.env['mail.activity'].sudo().create({
                'res_model_id': model_id,
                'res_id': order.id,
                'user_id': 6,
                'activity_type_id': activity_type.id,
                'summary': '有待审核的报价申请',
                'date_deadline': fields.Date.today(),
            })
            self.env['crm.lead'].search([('id', '=', opportunityid.id)]).write({
                'x_lead_status': '8',
            })
            self.audit_state = "audit"
            # 关闭报价页面  回到商机表单页面
            return {
                'type': 'ir.actions.act_window',
                'name': '报销账单',
                'res_model': 'crm.lead',
                'views': [[False, "form"]],
                "res_id": opportunityid.id,
                "target": "current",
            }

    # 同意报价
    def agree_quote_request_xks(self):
        print("同意报价")
        opportunityid = self.opportunity_id
        model_id = self.env['ir.model']._get(self._name).id
        activity_type = self.env['mail.activity.type'].search([('name', '=', 'reminder')])
        for order in self.ids:
            self.env['crm.lead'].search([('id', '=', opportunityid.id)]).write({
                'x_lead_status': '9',
            })
            # 删除线索转商机审核提醒
            self.env['mail.activity'].sudo().search([
                ('activity_type_id', '=', activity_type.id),
                ('res_id', '=', order),
                ('user_id', '=', self.env.user.id),
                ('res_model_id', '=', model_id)
            ]).unlink()
        self.audit_state = "agree"


    # 拒绝报价
    def reject_quote_request_xks(self):
        print("拒绝报价")
        opportunityid = self.opportunity_id
        model_id = self.env['ir.model']._get(self._name).id
        activity_type = self.env['mail.activity.type'].search([('name', '=', 'reminder')])
        for order in self.ids:
            self.env['crm.lead'].search([('id', '=', opportunityid.id)]).write({
                'x_lead_status': '10',
            })
            # 删除线索转商机审核提醒
            self.env['mail.activity'].sudo().search([
                ('activity_type_id', '=', activity_type.id),
                ('res_id', '=', order),
                ('user_id', '=', self.env.user.id),
                ('res_model_id', '=', model_id)
            ]).unlink()
        self.audit_state = "reject"


    @api.onchange('order_line')
    def onchange_order_ids(self):
        opportunity_id = self.opportunity_id
        sale_orders = self.env['sale.order'].search([('opportunity_id', '=', opportunity_id.id)], order='id desc')
        if len(sale_orders) > 0:
            sale_order_lines = sale_orders[0].order_line
            price = 0.0
            for line in sale_order_lines:
                price = price + line.price_unit*line.product_uom_qty
            self.env['crm.lead'].search([('id', '=', opportunity_id.id)]).write({'expected_revenue': price})
        for order in self:
            if order.advance_percentage:
                order.advance_total = float(order.amount_total) * float(order.advance_percentage)
            else:
                order.advance_total = None
            if order.middle_percentage:
                order.middle_total = float(order.amount_total) * float(order.middle_percentage)
            else:
                order.middle_total = None
            if order.balance_percentage:
                order.balance_total = float(order.amount_total) * float(order.balance_percentage)
            else:
                order.balance_total = None

    # 点击弹出发送报价单邮件页面
    def action_quotation_send(self):
        for cur_order_line in self.order_line:
            product_detail = self.env['product.template'].search([('id', '=', cur_order_line.product_template_id.id)])
            if cur_order_line.price_unit < product_detail.reserve_quote:
                msg = product_detail.name + '商品价格过低' if self.env.lang == 'zh_CN' else 'The Price is too low'
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': '提示',
                        'message': msg,
                        'sticky': False,  # 手动关闭   False 延时关闭
                        'className': 'bg-danger',  # 背景颜色  bg-success   bg-warning  bg-info
                    }
                }
        self.ensure_one()
        template_id = self._find_mail_template()
        lang = self.env.context.get('lang')
        template = self.env['mail.template'].browse(template_id)
        if template.lang:
            lang = template._render_lang(self.ids)[self.id]
        ctx = {
            'default_model': 'sale.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_paynow",
            'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            'model_description': self.with_context(lang=lang).type_name,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

