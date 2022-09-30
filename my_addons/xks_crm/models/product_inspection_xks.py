# -*- coding: UTF-8 -*-
from odoo import api, fields, models

class ProductInspectionXks(models.Model):
    _name = 'product.inspection.xks'
    _description = 'Product Inspection'

    name = fields.Char(string='Name')
    quantity = fields.Integer(string='Quantity') # 数量
    receive_time = fields.Date(string='Receive Time')  # 样品接受时间
    inspection_time = fields.Date(string='Inspection Time') # 验货时间
    inspection_description = fields.Text(string='Inspection Description')
    remark = fields.Text(string='Remark')
    is_qualified = fields.Boolean(string='Qualified', default=False)

    x_inspection_attachment_number = fields.Integer(compute='_compute_x_inspection_attachment_number',
                                                 string='Number of Inspection Attachments')  # 验货附件

    purchase_order_line_id = fields.Many2one('purchase.order.line', string='Purchase Order Line',
        change_default=True, ondelete='restrict', default=lambda self:self.env.context.get('purchase_order_line_id',False), required=True)

    def _compute_x_inspection_attachment_number(self):
        """验货附件上传"""
        attachment_data = self.env['ir.attachment'].read_group(
            [('res_model', '=', 'product.inspection.xks'), ('res_id', 'in', self.ids), ('description', '=', 'product.inspection.xks')], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for expense in self:
            expense.x_inspection_attachment_number = attachment.get(expense.id, 0)

    def action_get_inspection_attachment_view(self):
        """验货附件上传动作视图"""
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'product.inspection.xks'), ('res_id', 'in', self.ids), ('description', '=', 'product.inspection.xks')]
        res['context'] = {'default_res_model': 'product.inspection.xks', 'default_res_id': self.id, 'default_description': 'product.inspection.xks'}
        return res

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if vals['is_qualified']:
            # 修改采购当前状态为验货
            line = self.env['purchase.order.line'].sudo().search([
                ('id', '=', vals['purchase_order_line_id']),
            ])
            line.write({
                'current_state': '5',
            })
            order = self.env['crm.lead'].sudo().search([
                ('id', '=', line.order_id.opportunity_id.id),
            ])
            # 状态未到验货改成验货状态
            if order.stage_id.id < 10:
                order.write({
                    'stage_id': 10,
                    'x_lead_status': '70',
                })
        return res

    def write(self, vals):
        if 'is_qualified' in vals:
            if vals['is_qualified']:
                # 修改采购当前状态为验货
                line = self.env['purchase.order.line'].sudo().search([
                    ('id', '=', self.purchase_order_line_id.id),
                ])
                line.write({
                    'current_state': '5',
                })
                order = self.env['crm.lead'].sudo().search([
                    ('id', '=', line.order_id.opportunity_id.id),
                ])
                # 状态未到验货改成验货状态
                if order.stage_id.id < 10:
                    order.write({
                        'stage_id': 10,
                        'x_lead_status': '70',
                    })
        res = super().write(vals)
        return res