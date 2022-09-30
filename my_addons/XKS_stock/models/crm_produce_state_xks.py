# -*- coding: UTF-8 -*-
from odoo import api, fields, models
from datetime import date, timedelta

PRODUCE_STATE = [
    ('1', '待下单'),
    ('2', '签订合同'),
    ('3', '支付预付款'),
    ('4', '铸件，床身'),
    ('5', '电气，油路，气路等装配'),
    ('6', '制作夹具'),
    ('7', '工厂调试'),
    ('8', '验收'),
    ('9', '尾款'),
    ('10', '包装'),
    ('11', '发货'),
]

class CrmProduceStateXks(models.Model):
    _name = 'crm.produce.state.xks'
    _description = 'Produce State'

    name = fields.Selection(PRODUCE_STATE, string='State', index=True)
    sequence = fields.Integer(string='Sequence', default=20)
    operate_time = fields.Date(string='Operate Time', default=fields.Date.today)
    produce_state_attachment_number = fields.Integer(compute='_compute_produce_state_attachment_number', string='Number of Contract Attachments')
    produce_id = fields.Many2one('crm.produce.xks', string='Produce', ondelete='cascade', index=True, copy=False)

    def _compute_produce_state_attachment_number(self):
        """生产状态附件上传"""
        attachment_data = self.env['ir.attachment'].read_group(
            [('res_model', '=', self._name), ('res_id', 'in', self.ids), ('description', '=', 'crm.produce.state.xks')], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for expense in self:
            expense.x_contract_attachment_number = attachment.get(expense.id, 0)
    def action_get_produce_state_attachment_view(self):
        """合同附件上传动作视图"""
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', self._name), ('res_id', 'in', self.ids), ('description', '=', 'crm.produce.state.xks')]
        res['context'] = {'default_res_model': self._name, 'default_res_id': self.id, 'default_description': 'crm.produce.state.xks'}
        return res
