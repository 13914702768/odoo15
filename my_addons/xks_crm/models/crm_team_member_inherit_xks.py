# -*- coding: UTF-8 -*-
from odoo import api, fields, models

class CrmTeamMemberInheritXks(models.Model):
    _inherit = "crm.team.member"

    monthly_goal = fields.Float(string='Monthly Goal')
