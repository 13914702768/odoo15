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


class CrmProduceXks(models.Model):

    _name = 'crm.produce.xks'
    _description = 'Produce Xks'

    lead_id = fields.Many2one('crm.lead', string='Lead Reference', required=True, ondelete='cascade', index=True, copy=False)
    product_id = fields.Many2one(
        'product.product', string='Product', domain="[]")  # 产品
    product_template_id = fields.Many2one(
        'product.template', string='Product Template',
        related="product_id.product_tmpl_id", domain=[])
    # product_model_id = fields.Many2one(
    #     'product.model', string='Product Model',
    #     domain="['|', ('product_id', '=', False), ('product_id', '=', product_id)]",
    #     change_default=True, ondelete='restrict', check_company=True)  # 产品型号
    currency_id = fields.Many2one('res.currency',  readonly=True)
    price = fields.Float(string='Price', store=True, default=0.0)  # 单价
    buy_number = fields.Integer(string='Buy Number', default=1)  # 购买数量
    price_total = fields.Monetary(string='Total Price', store=True, currency_field='currency_id')
    advance_percentage = fields.Selection(
        PAYMENT_PERCENTAGE, string='Advance Percentage', index=True)
    advance_total = fields.Monetary(string='Advance Amount', store=True, compute='_amount_by_percentage', tracking=4, currency_field='currency_id')

    balance_percentage = fields.Selection(PAYMENT_PERCENTAGE, string='Balance Percentage', index=True)
    balance_total = fields.Monetary(string='Balance Amount', store=True, compute='_amount_by_percentage', tracking=4, currency_field='currency_id')

    factory_id = fields.Many2one('crm.supplier.xks', string='Supplier')
    x_contract_attachment_number = fields.Integer(compute='_compute_x_contract_attachment_number', string='Number of Contract Attachments')

    state_ids = fields.One2many('crm.produce.state.xks', 'produce_id', string='Produce State')

    remark = fields.Text(string='Remark')

    def _compute_x_contract_attachment_number(self):
        """合同附件上传"""
        attachment_data = self.env['ir.attachment'].read_group(
            [('res_model', '=', self._name), ('res_id', 'in', self.ids), ('description', '=', 'opportunity.produce.xks.contract')], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for expense in self:
            expense.x_contract_attachment_number = attachment.get(expense.id, 0)

    def action_get_contract_attachment_view(self):
        """合同附件上传动作视图"""
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', self._name), ('res_id', 'in', self.ids), ('description', '=', 'opportunity.produce.xks.contract')]
        res['context'] = {'default_res_model': self._name, 'default_res_id': self.id, 'default_description': 'opportunity.produce.xks.contract'}
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

