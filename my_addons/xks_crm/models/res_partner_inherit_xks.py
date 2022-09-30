# -*- coding: utf-8 -*-
from odoo import api, models, fields

CUSTOMER_LEVEL = [
    ('1', 'A Class'),
    ('2', 'B Class'),
    ('3', 'C Class'),
    ('4', 'D Class'),
]

class ResPartnerInheritXks(models.Model):
    _inherit = "res.partner"

    # 第一个参数为表   第二个参数为表中关联的字段ID
    leads_ids = fields.One2many('crm.lead', 'partner_id', string='Leads/Opportunity')

    # 拥有成交商机的数量
    transactions_number = fields.Integer(compute='_compute_number_transactions', string='Deal Count')

    x_level = fields.Selection(
        CUSTOMER_LEVEL, string='Level', index=True,
        default=CUSTOMER_LEVEL[0][0])

    # 行业
    x_industry = fields.Char(string='Industry')
    # 公司规模
    x_company_scale = fields.Char(string='Company Scale')

    @api.depends('leads_ids')
    def _compute_number_transactions(self):
        for record in self:
            number = 0
            leads = record.leads_ids
            for lead in leads:
                print(lead.stage_id.is_won)
                if lead.stage_id.is_won:
                    #是赢得阶段
                    number = number + 1
                else:
                    print("非赢得阶段")
            record.transactions_number = number

