# -*- coding: UTF-8 -*-
from odoo import api, fields, models

PRODUCE_STATE = [
    ('1', '铸件，床身'),
    ('2', '电气，油路，气路等装配'),
    ('3', '制作夹具'),
    ('4', '工厂调试'),
    ('5', '生产完成'),
]

class ProductProduceXks(models.Model):
    _name = 'product.produce.xks'
    _description = 'Product Produce'

    purchase_order_line_id = fields.Many2one('purchase.order.line', string='Purchase Order Line',
                                             change_default=True, ondelete='restrict',
                                             default=lambda self: self.env.context.get('purchase_order_line_id', False),
                                             required=True)
    pruduce_state = fields.Char(string='State')

    produce_complete = fields.Boolean(string="Produce Complete")
    update_time = fields.Date(string='Update Time', default=fields.Date.context_today)  # 修改时间
    remark = fields.Text(string='Remark')
    x_produce_img = fields.Html(string="Produce Img")
    x_produce_attachment_number = fields.Integer(compute='_compute_x_produce_attachment_number',
                                                    string='Number of Produce Attachments')  # 生产附件

    def action_get_produce_attachment_view(self):
        """生产附件上传动作视图"""
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'product.produce.xks'), ('res_id', 'in', self.ids), ('description', '=', 'product.produce.xks')]
        res['context'] = {'default_res_model': 'product.produce.xks', 'default_res_id': self.id, 'default_description': 'product.produce.xks'}
        return res

    @api.model
    def create(self, vals):
        if 'produce_complete' in vals:
            if vals['produce_complete']:
                # 修改采购当前状态为验货
                line = self.env['purchase.order.line'].sudo().search([('id', '=', vals['purchase_order_line_id'])])
                line.write({'current_state': '4'})
                order = self.env['crm.lead'].sudo().search([('id', '=', line.order_id.opportunity_id.id)])
                # 状态未到验货改成验货状态
                if order.stage_id.id < 9:
                    order.write({
                        'stage_id': 9,
                        'x_lead_status': '60',
                    })
                # 删除财务预付款支付完成提醒
                self.env['mail.activity'].sudo().search([
                    ('activity_type_id', '=', self.env['mail.activity.type'].search(
                        ['|', ('name', '=', '待办'), ('name', '=', 'To Do')]).id),
                    ('res_id', '=', line.order_id.id),
                    ('user_id', '=', self.env.user.id),
                    ('res_model_id', '=', self.env['ir.model']._get('purchase.order').id),
                    ('summary', '=', '采购订单预付款支付成功' if self.env.lang == 'zh_CN' else 'Purchase Order Advance Pay Success')
                ]).unlink()
        res = super().create(vals)
        return res

    def write(self, vals):
        if 'produce_complete' in vals:
            if vals['produce_complete']:
                # 修改采购当前状态为验货
                line = self.env['purchase.order.line'].sudo().search([ ('id', '=', self.purchase_order_line_id.id)])
                line.write({'current_state': '4'})
                # 删除财务预付款支付完成提醒
                self.env['mail.activity'].sudo().search([
                    ('activity_type_id', '=', self.env['mail.activity.type'].search(
                        ['|', ('name', '=', '待办'), ('name', '=', 'To Do')]).id),
                    ('res_id', '=', self.purchase_order_line_id.order_id.id),
                    ('user_id', '=', self.env.user.id),
                    ('res_model_id', '=', self.env['ir.model']._get('purchase.order').id),
                    (
                        'summary', '=',
                        '采购订单预付款支付成功' if self.env.lang == 'zh_CN' else 'Purchase Order Advance Pay Success')
                ]).unlink()
                order = self.env['crm.lead'].sudo().search([('id', '=', line.order_id.opportunity_id.id)])
                # 状态未到验货改成验货状态
                if order.stage_id.id < 9:
                    order.write({
                        'stage_id': 9,
                        'x_lead_status': '60',
                    })
        res = super().write(vals)
        return res