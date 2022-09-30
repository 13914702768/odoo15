""""CRM Dashboard"""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import datetime
import calendar
import time

from odoo import models, fields, api
from odoo.tools import date_utils
from odoo.http import request

from dateutil.relativedelta import relativedelta
from datetime import datetime


class CRMSalesTeam(models.Model):
    _inherit = 'crm.team'

    crm_lead_state_id = fields.Many2one("crm.stage", string="CRM Lead",
                                        store=True)


class ResUser(models.Model):
    _inherit = 'res.users'

    sales = fields.Float(string="Target")


class SalesOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        """Supering the Confirm Button for Changing CRM Stage"""
        res = super(SalesOrder, self).action_confirm()
        self.opportunity_id.stage_id = self.team_id.crm_lead_state_id
        return res


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    monthly_goal = fields.Float(string="Monthly Goal")
    achievement_amount = fields.Float(string="Monthly Achievement")

    @api.model
    def _get_currency(self):
        currency_array = [self.env.user.company_id.currency_id.symbol,
                          self.env.user.company_id.currency_id.position]
        return currency_array

    @api.model
    def check_user_group(self):
        """Checking user group"""
        user = self.env.user
        if user.has_group('sales_team.group_sale_manager'):
            return True
        else:
            return False

    @api.model
    def check_user_group_team(self):
        """Checking user group team"""
        user = self.env.user
        if user.has_group('sales_team.group_sale_salesman_all_leads'):
            return True
        else:
            return False

    # 漏斗（Funnel Chart）
    @api.model
    def get_lead_stage_data(self, user_id):
        """funnel chart"""
        stage_ids = self.env["crm.stage"].search([])
        crm_list = []
        if user_id == None:
            user_id = '0'
        for stage in stage_ids:
            if user_id != '0':
                if self.env.user.has_group('sales_team.group_sale_manager') or self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
                    leads = self.search_count([("stage_id", "=", stage.id), ("user_id", "=", int(user_id))])
                else:
                    leads = self.search_count([("stage_id", "=", stage.id), ("user_id", "!=", None)])
            else:
                leads = self.search_count([("stage_id", "=", stage.id), ("user_id", "!=", None)])
            # if leads != 0:
            #     crm_list.append((stage.name, int(leads)))
            crm_list.append((stage.name, int(leads)))
        return crm_list

    # 阅读需求数(Leads by Month)
    @api.model
    def get_lead_month_pie(self, user_id):
        if user_id is None:
            user_id = "0"
        """pie chart"""
        month_count = []
        month_value = []
        current_year = int(time.strftime('%Y', time.localtime(time.time())))
        leads = self.env['crm.lead'].search([])
        for rec in leads:
            if current_year == rec.create_date.year:
                if user_id != "0":
                    if user_id == str(rec.user_id.id):
                        month = rec.create_date.month
                        if month not in month_value:
                            month_value.append(month)
                        month_count.append(month)
                else:
                    month = rec.create_date.month
                    if month not in month_value:
                        month_value.append(month)
                    month_count.append(month)
        month_value.sort()
        month_val = []
        for index in range(len(month_value)):
            value = month_count.count(month_value[index])
            month_name = calendar.month_name[month_value[index]]
            month_val.append({'label': month_name, 'value': value})
        name = []
        for record in month_val:
            name.append(record.get('label'))
        count = []
        for record in month_val:
            count.append(record.get('value'))
        month = [count, name]
        return month

    # 待完成的活动（CRM Activity）
    @api.model
    def get_the_sales_activity(self, user_id):
        """Sales Activity Pie"""
        if user_id == None:
            user_id = '0'
        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != '0':
                self._cr.execute('''select mail_activity_type.name,COUNT(*) from mail_activity
                                    inner join mail_activity_type on mail_activity.activity_type_id = mail_activity_type.id
                                    where mail_activity.res_model = 'crm.lead' and mail_activity.user_id = %s
                                    GROUP BY mail_activity_type.name ''' % user_id)
            else:
                self._cr.execute('''select mail_activity_type.name,COUNT(*) from mail_activity
                                    inner join mail_activity_type on mail_activity.activity_type_id = mail_activity_type.id
                                    where mail_activity.res_model = 'crm.lead' GROUP BY mail_activity_type.name''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != '0':
                self._cr.execute('''select mail_activity_type.name,COUNT(*) from mail_activity
                                                    inner join mail_activity_type on mail_activity.activity_type_id = mail_activity_type.id
                                                    where mail_activity.res_model = 'crm.lead' and mail_activity.user_id = %s 
                                                    GROUP BY mail_activity_type.name ''' % user_id)
            else:
                self._cr.execute('''select mail_activity_type.name,COUNT(*) from mail_activity
                                    inner join mail_activity_type on mail_activity.activity_type_id = mail_activity_type.id
                                    where mail_activity.res_model = 'crm.lead' and mail_activity.user_id in 
                                    (select crm_team_member.user_id from crm_team_member, crm_team where crm_team.user_id = %s
                                            and crm_team.id = crm_team_member.crm_team_id and crm_team_member.active = true
                                            and crm_team.active = true)
                                    GROUP BY mail_activity_type.name ''' % self.env.uid)
        else:
            self._cr.execute('''select mail_activity_type.name,COUNT(*) from mail_activity
                    inner join mail_activity_type on mail_activity.activity_type_id = mail_activity_type.id
                    where mail_activity.res_model = 'crm.lead' and mail_activity.user_id = %s
                    GROUP BY mail_activity_type.name''' % self.env.uid)
        data = self._cr.dictfetchall()

        name = []
        for record in data:
            name.append(record.get('name'))

        count = []
        for record in data:
            count.append(record.get('count'))

        final = [count, name]
        return final

    # 目标（Year to Date）
    @api.model
    def get_the_annual_target(self):
        """Annual Target: Year To Date Graph"""
        session_user_id = self.env.uid

        self._cr.execute('''SELECT res_users.id,res_users.sales,res_users.sale_team_id,
        (SELECT crm_team.invoiced_target FROM crm_team WHERE crm_team.id = res_users.sale_team_id)
        FROM res_users WHERE res_users.sales is not null and res_users.id=%s
        AND res_users.sale_team_id is not null''' % session_user_id)
        data2 = self._cr.dictfetchall()

        sales = []
        inv_target = []
        team_id = 0
        for rec in data2:
            sales.append(rec['sales'])
            inv_target.append(rec['invoiced_target'])
            if inv_target == [None]:
                inv_target = [0]
            team_id = rec['sale_team_id']
        target_annual = (sum(sales) + sum(inv_target))

        if self.env.user.has_group('sales_team.group_sale_manager'):
            self._cr.execute('''SELECT res_users.id,res_users.sales,res_users.sale_team_id,
            (SELECT crm_team.invoiced_target FROM crm_team WHERE
            crm_team.id = res_users.sale_team_id) FROM res_users WHERE res_users.id = %s
            AND res_users.sales is not null;''' % session_user_id)
            data3 = self._cr.dictfetchall()

            sales = []
            inv_target = []
            for rec in data3:
                sales.append(rec['sales'])
                inv_target.append(rec['invoiced_target'])
                if inv_target == [None]:
                    inv_target = [0]
            ytd_target = (sum(sales) + sum(inv_target))

            self._cr.execute('''select sum(expected_revenue) from crm_lead where stage_id=4
            and team_id=%s AND Extract(Year FROM date_closed)=Extract(Year FROM DATE(NOW(
            )))''' % team_id)
            achieved_won_data = self._cr.dictfetchall()
            achieved_won = [item['sum'] for item in achieved_won_data]

        else:
            self._cr.execute('''SELECT res_users.id,res_users.sales FROM res_users
            WHERE res_users.id = %s AND res_users.sales is not null;''' % session_user_id)
            data4 = self._cr.dictfetchall()

            sales = []
            for rec in data4:
                sales.append(rec['sales'])
            ytd_target = (sum(sales))

            self._cr.execute('''select sum(expected_revenue) from crm_lead where stage_id=4
            and user_id=%s AND Extract(Year FROM date_closed)=Extract(Year FROM DATE(NOW(
            )))''' % session_user_id)
            achieved_won_data = self._cr.dictfetchall()
            achieved_won = [item['sum'] for item in achieved_won_data]

        won = achieved_won[0]
        if won is None:
            won = 0
        # value = [target_annual, ytd_target, won]
        value = [200000, 130000, 120000, 200000, 130000, 120000]
        name = ["Annual Target", "YtD target", "Won","Annual Target2", "YtD target2", "Won2"]
        final = [value, name]

        return final

    #销售业绩
    @api.model
    def get_sales_performance(self, team_id, type):
        session_user_id = self.env.uid
        if type is None:
            type = "1"
        if team_id is None:
            team_id = "0"
        if self.env.user.has_group('sales_team.group_sale_manager'):
            if type == "1":
                if team_id != '0':
                    self._cr.execute('''select crm_team.id team_id, crm_team.name team_name, crm_team_member.user_id, res_partner.name user_name
                                                        ,COALESCE((select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                                                            crm_lead.user_id = crm_team_member.user_id and type='opportunity' and active='true' AND Extract(
                                                            MONTH FROM crm_lead.date_closed) = Extract(MONTH FROM DATE(NOW())) AND
                                                            Extract(Year FROM crm_lead.date_closed) = Extract(Year FROM DATE(NOW()))
                                                            and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')), 0) performance
                                                    from crm_team, crm_team_member, res_users, res_partner
                                    	            where crm_team.active = true and crm_team_member.active = true 
                                                        and crm_team_member.crm_team_id = crm_team.id and res_users.id = crm_team_member.user_id 
                                    	                and res_users.partner_id = res_partner.id
                                    	                and crm_team.id = %s ''' % team_id)
                else:
                    self._cr.execute('''select crm_team.id team_id, crm_team.name team_name, crm_team_member.user_id, res_partner.name user_name
                                                        ,COALESCE((select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                                                            crm_lead.user_id = crm_team_member.user_id and type='opportunity' and active='true' AND Extract(
                                                            MONTH FROM crm_lead.date_closed) = Extract(MONTH FROM DATE(NOW())) AND
                                                            Extract(Year FROM crm_lead.date_closed) = Extract(Year FROM DATE(NOW()))
                                                            and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')), 0) performance
                                                    from crm_team, crm_team_member, res_users, res_partner
                                    	            where crm_team.active = true and crm_team_member.active = true 
                                                        and crm_team_member.crm_team_id = crm_team.id and res_users.id = crm_team_member.user_id 
                                    	                and res_users.partner_id = res_partner.id ''')
            else:
                if team_id != '0':
                    self._cr.execute('''select crm_team.id team_id, crm_team.name team_name, crm_team_member.user_id, res_partner.name user_name
                                                        ,COALESCE((select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                                                            crm_lead.user_id = crm_team_member.user_id and type='opportunity' and active='true' 
                                                            AND Extract(Year FROM crm_lead.date_closed) = Extract(Year FROM DATE(NOW()))
                                                            and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')), 0) performance
                                                    from crm_team, crm_team_member, res_users, res_partner
                                    	            where crm_team.active = true and crm_team_member.active = true 
                                                        and crm_team_member.crm_team_id = crm_team.id and res_users.id = crm_team_member.user_id 
                                    	                and res_users.partner_id = res_partner.id
                                    	                and crm_team.id = %s ''' % team_id)
                else:
                    self._cr.execute('''select crm_team.id team_id, crm_team.name team_name, crm_team_member.user_id, res_partner.name user_name
                                                        ,COALESCE((select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                                                            crm_lead.user_id = crm_team_member.user_id and type='opportunity' and active='true' 
                                                            AND Extract(Year FROM crm_lead.date_closed) = Extract(Year FROM DATE(NOW()))
                                                            and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')), 0) performance
                                                    from crm_team, crm_team_member, res_users, res_partner
                                    	            where crm_team.active = true and crm_team_member.active = true 
                                                        and crm_team_member.crm_team_id = crm_team.id and res_users.id = crm_team_member.user_id 
                                    	                and res_users.partner_id = res_partner.id''')
        else:
            if type == "1":
                self._cr.execute('''select crm_team.id team_id, crm_team.name team_name, crm_team_member.user_id, res_partner.name user_name
                                                ,COALESCE((select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                                                    crm_lead.user_id = crm_team_member.user_id and type='opportunity' and active='true' 
                                                    AND Extract(MONTH FROM crm_lead.date_closed) = Extract(MONTH FROM DATE(NOW())) AND
                                                    Extract(Year FROM crm_lead.date_closed) = Extract(Year FROM DATE(NOW()))
                                                    and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')), 0) performance
                                            from crm_team, crm_team_member, res_users, res_partner
                            	            where crm_team.active = true and crm_team_member.active = true 
                                                and crm_team_member.crm_team_id = crm_team.id and res_users.id = crm_team_member.user_id 
                            	                and res_users.partner_id = res_partner.id 
                            	                and crm_team.id in (select id team_id from crm_team where user_id = %s union select crm_team_id team_id from crm_team_member where user_id = %s)
                            	                ''', (session_user_id, session_user_id))
            else:
                self._cr.execute('''select crm_team.id team_id, crm_team.name team_name, crm_team_member.user_id, res_partner.name user_name
                                                ,COALESCE((select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                                                    crm_lead.user_id = crm_team_member.user_id and type='opportunity' and active='true' 
                                                    AND Extract(Year FROM crm_lead.date_closed) = Extract(Year FROM DATE(NOW()))
                                                    and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')), 0) performance
                                            from crm_team, crm_team_member, res_users, res_partner
                            	            where crm_team.active = true and crm_team_member.active = true 
                                                and crm_team_member.crm_team_id = crm_team.id and res_users.id = crm_team_member.user_id 
                            	                and res_users.partner_id = res_partner.id
                            	                and crm_team.id in (select id team_id from crm_team where user_id = %s union select crm_team_id team_id from crm_team_member where user_id = %s)
                            	                ''', (session_user_id, session_user_id))
        data = self._cr.dictfetchall()

        value = []
        name = []
        for rec in data:
            value.append(rec['performance'])
            name.append(rec['user_name'])

        final = [value, name]
        return final

    @api.model
    def get_the_campaign_pie(self):
        """Leads Group By Campaign Pie"""
        self._cr.execute('''select campaign_id, COUNT(*),
        (SELECT name FROM utm_campaign WHERE utm_campaign.id = crm_lead.campaign_id)
        FROM crm_lead WHERE campaign_id is not null GROUP BY campaign_id''')
        data = self._cr.dictfetchall()

        name = []
        for record in data:
            name.append(record.get('name'))

        count = []
        for record in data:
            count.append(record.get('count'))

        final = [count, name]
        return final

    @api.model
    def get_the_source_pie(self):
        """Leads Group By Source Pie"""
        self._cr.execute('''select source_id,COUNT(*),(SELECT name FROM utm_source
        WHERE utm_source.id = crm_lead.source_id) from crm_lead
        WHERE source_id is not null GROUP BY source_id''')
        data = self._cr.dictfetchall()

        name = []
        for record in data:
            name.append(record.get('name'))

        count = []
        for record in data:
            count.append(record.get('count'))

        final = [count, name]
        return final

    @api.model
    def get_the_medium_pie(self):
        """Leads Group By Medium Pie"""
        self._cr.execute('''select medium_id,COUNT(*),(SELECT name FROM utm_medium
        WHERE utm_medium.id = crm_lead.medium_id) from crm_lead
        WHERE medium_id is not null GROUP BY medium_id ''')
        data = self._cr.dictfetchall()

        name = []
        for record in data:
            name.append(record.get('name'))

        count = []
        for record in data:
            count.append(record.get('count'))

        final = [count, name]
        return final

    # 销售总收入(Total Revenue by Salesperson   商机总额-赢得   赢得  归档的)
    @api.model
    def revenue_count_pie(self, user_id):
        """Total expected revenue and count Pie"""
        session_user_id = self.env.uid
        if user_id is None:
            user_id = "0"
        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != "0":
                self._cr.execute('''select sum(expected_revenue) as revenue from crm_lead
                                    where type='opportunity' and active=true and user_id = %s 
                                    ''' % user_id)
            else:
                self._cr.execute('''select sum(expected_revenue) as revenue from crm_lead
                                    where type='opportunity' and active=true''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != "0":
                self._cr.execute('''select sum(expected_revenue) as revenue from crm_lead
                                    where user_id = %s and type='opportunity' and active=true'''% user_id)
            else:
                self._cr.execute('''select sum(expected_revenue) as revenue from crm_lead
                                                    where ((crm_lead.user_id in 
                                                             (select crm_team_member.user_id from crm_team_member, crm_team where crm_team.user_id = %s 
                                                                and crm_team.id = crm_team_member.crm_team_id 
                                                                and crm_team_member.active = true and crm_team.active = true))
                                            			   OR (crm_lead.user_id is NULL AND crm_lead.team_id IN 
                                            			        (select id from crm_team where crm_team.user_id = %s))
                                            			   )
                                                    and type='opportunity' and active=true''',
                                 (session_user_id, session_user_id))
        else:
            self._cr.execute('''select sum(expected_revenue) as revenue from crm_lead
                    where user_id=%s and type='opportunity' and active=true''' % session_user_id)
        total_expected_revenue_data = self._cr.dictfetchall()
        total_expected_revenue = [item['revenue'] for item in total_expected_revenue_data]
        total_expected_revenue = total_expected_revenue[0]
        if total_expected_revenue is None:
            total_expected_revenue = 0

        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != "0":
                self._cr.execute('''select sum(expected_revenue) as revenue from crm_lead
                                         where type='opportunity' and user_id = %s
                                         and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                ''' % user_id)
            else:
                self._cr.execute('''select sum(expected_revenue) as revenue from crm_lead
                                                where type='opportunity' 
                                                and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                                ''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != "0":
                self._cr.execute('''select sum(expected_revenue) as revenue from crm_lead
                                          where user_id = %s and type='opportunity' 
                                          and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                 '''% user_id)
            else:
                self._cr.execute('''select sum(expected_revenue) as revenue from crm_lead
                                                where ((crm_lead.user_id in 
                                                        (select crm_team_member.user_id from crm_team_member, crm_team where crm_team.user_id = %s 
                                                            and crm_team.id = crm_team_member.crm_team_id 
                                                            and crm_team_member.active = true and crm_team.active = true))
                            			                  OR (crm_lead.user_id is NULL AND crm_lead.team_id IN 
                            			                       (select id from crm_team where crm_team.user_id = %s))
                            			               )
                                                and type='opportunity' 
                                                and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                                ''', (session_user_id, session_user_id))
        else:
            self._cr.execute('''select sum(expected_revenue) as revenue from crm_lead
                    where user_id=%s and type='opportunity' 
                    and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                    ''' % session_user_id)

        total_won_rev_data = self._cr.dictfetchall()
        total_won_rev = [item['revenue'] for item in total_won_rev_data]
        total_won_rev = total_won_rev[0]
        if total_won_rev is None:
            total_won_rev = 0

        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != "0":
                self._cr.execute('''select sum(expected_revenue) as revenue from crm_lead
                                    where type='opportunity' and active='false' and user_id = %s ''' % user_id)
            else:
                self._cr.execute('''select sum(expected_revenue) as revenue from crm_lead
                                    where type='opportunity' and active='false' ''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != "0":
                self._cr.execute('''select sum(expected_revenue) as revenue from crm_lead
                                    where user_id = %s and type='opportunity' and active='false'
                                    ''' % user_id)
            else:
                self._cr.execute('''select sum(expected_revenue) as revenue from crm_lead
                                    where ((crm_lead.user_id in 
                                               (select crm_team_member.user_id from crm_team_member, crm_team where crm_team.user_id = %s 
                                                      and crm_team.id = crm_team_member.crm_team_id 
                                                      and crm_team_member.active = true and crm_team.active = true))
                            			     OR (crm_lead.user_id is NULL AND crm_lead.team_id IN 
                            			              (select id from crm_team where crm_team.user_id = %s))
                            			   ) 
                                    and type='opportunity' and active='false'
                                    ''', (session_user_id, session_user_id))
        else:
            self._cr.execute('''select sum(expected_revenue) as revenue from crm_lead
                    where user_id=%s and type='opportunity' and active='false'
                    ''' % session_user_id)
        total_lost_rev_data = self._cr.dictfetchall()
        total_lost_rev = [item['revenue'] for item in total_lost_rev_data]
        total_lost_rev = total_lost_rev[0]
        if total_lost_rev is None:
            total_lost_rev = 0

        exp_revenue_without_won = total_expected_revenue - total_won_rev
        revenue_pie_count = [exp_revenue_without_won, total_won_rev, total_lost_rev]
        revenue_pie_title = ['Expected without Won', 'Won', 'Lost']
        revenue_data = [revenue_pie_count, revenue_pie_title]

        return revenue_data

    # 查询团队成员列表
    @api.model
    def get_user_list(self):
        session_user_id = self.env.uid
        if self.env.user.has_group('sales_team.group_sale_manager'):
            self._cr.execute('''select res_users.id, res_partner.name from res_users, res_partner  
                                     where res_users.partner_id = res_partner.id 
                                and res_users.active = true and res_partner.active = true ''' )
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            self._cr.execute('''select res_users.id, res_partner.name from res_users, res_partner  
                                                 where  res_users.id in (select crm_team_member.user_id 
                                                   from crm_team_member, crm_team where crm_team.user_id = '%s'
                                                   and crm_team.id = crm_team_member.crm_team_id 
                                                   and crm_team_member.active = true
                                                   and crm_team.active = true)
                                            and res_users.partner_id = res_partner.id 
                                            and res_users.active = true and res_partner.active = true
                        ''' % session_user_id)
        else:
            self._cr.execute('''select res_users.id, res_partner.name from res_users, res_partner  
                                       where res_users.id = '%s' and res_users.partner_id = res_partner.id 
                                       and res_users.active = true and res_partner.active = true
                        ''' % session_user_id)
        data = self._cr.fetchall()
        users = []
        for user in data:
            user_list = list(user)
            users.append(user_list)
        if self.env.user.has_group('sales_team.group_sale_manager'):
            self._cr.execute('''SELECT ID, NAME FROM CRM_TEAM WHERE ACTIVE = TRUE''')
        else:
            self._cr.execute('''SELECT ID, NAME FROM CRM_TEAM WHERE ACTIVE = TRUE and ID in
                    (select id team_id from crm_team where user_id = %s union 
                    select crm_team_id team_id from crm_team_member where user_id = %s)
             ''', (session_user_id, session_user_id))
        team_data = self._cr.fetchall()
        teams = []
        for team in team_data:
            team_list = list(team)
            teams.append(team_list)
        return {
            'team_users': users,
            'teams': teams
        }

    @api.model
    def get_goal_time_list(self):
        # 当前月
        current_month = int(time.strftime('%m', time.localtime(time.time())))
        month_times = [[1, 'January', current_month], [2, 'February', current_month], [3, 'March', current_month],
                       [4, 'April', current_month], [5, 'May', current_month], [6, 'June', current_month], [7, 'July', current_month],
                       [8, 'August', current_month], [9, 'September', current_month], [10, 'October', current_month],
                       [11, 'November', current_month], [12, 'December', current_month]]
        current_quarter = 1
        if current_month < 4:
            current_quarter = 1
        elif current_month < 7:
            current_quarter = 2
        elif current_month < 10:
            current_quarter = 3
        else:
            current_quarter = 4
        quarter_times = [[1, 'First Quarter', current_quarter], [2, 'Second Quarter', current_quarter],
                         [3, 'Third Quarter', current_quarter], [4, 'Fourth Quarter', current_quarter]]
        current_year = int(time.strftime('%Y', time.localtime(time.time())))
        year_times = [[current_year, str(current_year), current_year], [current_year - 1, str(current_year - 1), current_year]]
        return {'month_times': month_times,
                'quarter_times': quarter_times,
                'year_times': year_times}

    # 初始化活动列表（Upcoming Activities）
    @api.model
    def get_upcoming_events(self):
        """Upcoming Activities Table"""
        today = fields.date.today()
        session_user_id = self.env.uid
        if self.env.user.has_group('sales_team.group_sale_manager'):
            # AND mail_activity.date_deadline >= '%s'
            self._cr.execute('''select mail_activity.activity_type_id,mail_activity.date_deadline,
                    mail_activity.summary,mail_activity.res_name,(SELECT mail_activity_type.name
                    FROM mail_activity_type WHERE mail_activity_type.id = mail_activity.activity_type_id),
                    mail_activity.user_id ,(select res_partner.name from res_users, res_partner 
                    where res_users.id = mail_activity.user_id and res_users.partner_id = res_partner.id),mail_activity.res_id
                    FROM mail_activity WHERE res_model = 'crm.lead' 
                    GROUP BY mail_activity.activity_type_id,
                    mail_activity.date_deadline,mail_activity.summary,mail_activity.res_name,mail_activity.user_id, mail_activity.res_id
                    order by mail_activity.date_deadline asc''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            self._cr.execute('''select mail_activity.activity_type_id,mail_activity.date_deadline,
                    mail_activity.summary,mail_activity.res_name,(SELECT mail_activity_type.name
                    FROM mail_activity_type WHERE mail_activity_type.id = mail_activity.activity_type_id),
                    mail_activity.user_id ,(select res_partner.name from res_users, res_partner 
                    where res_users.id = mail_activity.user_id and res_users.partner_id = res_partner.id),mail_activity.res_id
                    FROM mail_activity WHERE res_model = 'crm.lead' and mail_activity.user_id in 
                    (select crm_team_member.user_id from crm_team_member, crm_team where crm_team.user_id = '%s'
                            and crm_team.id = crm_team_member.crm_team_id and crm_team_member.active = true and crm_team.active = true)
                    GROUP BY mail_activity.activity_type_id,
                    mail_activity.date_deadline,mail_activity.summary,mail_activity.res_name,mail_activity.user_id, mail_activity.res_id
                    order by mail_activity.date_deadline asc''' % session_user_id)
        else:
            self._cr.execute('''select mail_activity.activity_type_id,mail_activity.date_deadline,
                    mail_activity.summary,mail_activity.res_name,(SELECT mail_activity_type.name
                    FROM mail_activity_type WHERE mail_activity_type.id = mail_activity.activity_type_id),
                    mail_activity.user_id ,(select res_partner.name from res_users, res_partner 
                    where res_users.id = mail_activity.user_id and res_users.partner_id = res_partner.id),mail_activity.res_id
                    FROM mail_activity WHERE res_model = 'crm.lead' and user_id = %s GROUP BY mail_activity.activity_type_id,
                    mail_activity.date_deadline,mail_activity.summary,mail_activity.res_name,mail_activity.user_id, mail_activity.res_id
                    order by mail_activity.date_deadline asc''' % session_user_id)
        data = self._cr.fetchall()

        events = []
        for record in data:
            # user_id = record[5]
            # user_id_obj = self.env['res.users'].browse(user_id)
            record_list = list(record)
            # record_list[5] = user_id_obj.name
            events.append(record_list)

        return {'event': events}

    # 查询活动列表（Upcoming Activities）
    @api.model
    def search_upcoming_events(self, user_id):
        """Upcoming Activities Table"""
        today = fields.date.today()
        session_user_id = self.env.uid
        if user_id is None:
            user_id = "0"
        if self.env.user.has_group('sales_team.group_sale_manager'):
            # AND mail_activity.date_deadline >= '%s'
            if user_id != "0":
                self._cr.execute('''select mail_activity.activity_type_id,mail_activity.date_deadline,
                                        mail_activity.summary,mail_activity.res_name,(SELECT mail_activity_type.name
                                        FROM mail_activity_type WHERE mail_activity_type.id = mail_activity.activity_type_id),
                                        mail_activity.user_id ,(select res_partner.name from res_users, res_partner 
                                        where res_users.id = mail_activity.user_id and res_users.partner_id = res_partner.id),mail_activity.res_id
                                        FROM mail_activity WHERE res_model = 'crm.lead' and mail_activity.user_id = %s
                                        GROUP BY mail_activity.activity_type_id,
                                        mail_activity.date_deadline,mail_activity.summary,mail_activity.res_name,mail_activity.user_id, mail_activity.res_id
                                        order by mail_activity.date_deadline asc'''% user_id)
            else:
                self._cr.execute('''select mail_activity.activity_type_id,mail_activity.date_deadline,
                                        mail_activity.summary,mail_activity.res_name,(SELECT mail_activity_type.name
                                        FROM mail_activity_type WHERE mail_activity_type.id = mail_activity.activity_type_id),
                                        mail_activity.user_id ,(select res_partner.name from res_users, res_partner 
                                        where res_users.id = mail_activity.user_id and res_users.partner_id = res_partner.id),mail_activity.res_id
                                        FROM mail_activity WHERE res_model = 'crm.lead' 
                                        GROUP BY mail_activity.activity_type_id,
                                        mail_activity.date_deadline,mail_activity.summary,mail_activity.res_name,mail_activity.user_id, mail_activity.res_id
                                        order by mail_activity.date_deadline asc''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != "0":
                self._cr.execute('''select mail_activity.activity_type_id,mail_activity.date_deadline,
                                        mail_activity.summary,mail_activity.res_name,(SELECT mail_activity_type.name
                                        FROM mail_activity_type WHERE mail_activity_type.id = mail_activity.activity_type_id),
                                        mail_activity.user_id ,(select res_partner.name from res_users, res_partner 
                                        where res_users.id = mail_activity.user_id and res_users.partner_id = res_partner.id),mail_activity.res_id
                                        FROM mail_activity WHERE res_model = 'crm.lead' and mail_activity.user_id = %s
                                        GROUP BY mail_activity.activity_type_id,
                                        mail_activity.date_deadline,mail_activity.summary,mail_activity.res_name,mail_activity.user_id, mail_activity.res_id
                                        order by mail_activity.date_deadline asc''' % user_id)
            else:
                self._cr.execute('''select mail_activity.activity_type_id,mail_activity.date_deadline,
                                        mail_activity.summary,mail_activity.res_name,(SELECT mail_activity_type.name
                                        FROM mail_activity_type WHERE mail_activity_type.id = mail_activity.activity_type_id),
                                        mail_activity.user_id ,(select res_partner.name from res_users, res_partner 
                                        where res_users.id = mail_activity.user_id and res_users.partner_id = res_partner.id),mail_activity.res_id
                                        FROM mail_activity WHERE res_model = 'crm.lead' and mail_activity.user_id in 
                                        (select crm_team_member.user_id from crm_team_member, crm_team where crm_team.user_id = '%s'
                                                and crm_team.id = crm_team_member.crm_team_id and crm_team_member.active = true and crm_team.active = true)
                                        GROUP BY mail_activity.activity_type_id,
                                        mail_activity.date_deadline,mail_activity.summary,mail_activity.res_name,mail_activity.user_id, mail_activity.res_id
                                        order by mail_activity.date_deadline asc''' % session_user_id)
        else:
            self._cr.execute('''select mail_activity.activity_type_id,mail_activity.date_deadline,
                        mail_activity.summary,mail_activity.res_name,(SELECT mail_activity_type.name
                        FROM mail_activity_type WHERE mail_activity_type.id = mail_activity.activity_type_id),
                        mail_activity.user_id ,(select res_partner.name from res_users, res_partner 
                        where res_users.id = mail_activity.user_id and res_users.partner_id = res_partner.id),mail_activity.res_id
                        FROM mail_activity WHERE res_model = 'crm.lead' and user_id = %s GROUP BY mail_activity.activity_type_id,
                        mail_activity.date_deadline,mail_activity.summary,mail_activity.res_name,mail_activity.user_id, mail_activity.res_id
                        order by mail_activity.date_deadline asc''' % session_user_id)
        data = self._cr.fetchall()

        events = []
        for record in data:
            # user_id = record[5]
            # user_id_obj = self.env['res.users'].browse(user_id)
            record_list = list(record)
            # record_list[5] = user_id_obj.name
            events.append(record_list)

        return {'event': events}

    @api.model
    def get_top_deals(self):
        """Top 10 Deals Table"""
        self._cr.execute('''SELECT crm_lead.user_id,crm_lead.id,crm_lead.expected_revenue,
        crm_lead.name,crm_lead.company_id, (SELECT crm_team.name FROM crm_team
        WHERE crm_lead.team_id = crm_team.id) from crm_lead where crm_lead.expected_revenue
        is not null and crm_lead.type = 'opportunity' GROUP BY crm_lead.user_id,
        crm_lead.id,crm_lead.expected_revenue,crm_lead.name,crm_lead.company_id
        order by crm_lead.expected_revenue DESC limit 10''')
        data1 = self._cr.fetchall()

        deals = []
        num = 0
        for rec in data1:
            company_id = rec[4]
            user_id = rec[0]
            company_id_obj = self.env['res.company'].browse(company_id)
            user_id_obj = self.env['res.users'].browse(user_id)
            currency = company_id_obj.currency_id.symbol
            rec_list = list(rec)
            rec_list[0] = user_id_obj.name
            num += 1
            rec_list.append(currency)
            rec_list.append(num)
            deals.append(rec_list)

        return {'deals': deals}

    # 初始化本月目标与完成（Monthly Goal）
    @api.model
    def get_monthly_goal(self):
        """Monthly Goal Gauge"""
        uid = request.session.uid

        if self.env.user.has_group('sales_team.group_sale_manager'):
            self._cr.execute('''select SUM(COALESCE(crm_lead.expected_revenue, 0)) as expected_revenue
                                from crm_lead where crm_lead.date_closed is not null 
                                AND crm_lead.type = 'opportunity' and crm_lead.active='true' 
                                and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31') 
                                AND Extract(MONTH FROM crm_lead.date_closed) = Extract(MONTH FROM DATE(NOW()))''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            self._cr.execute('''select SUM(COALESCE(crm_lead.expected_revenue, 0)) as expected_revenue
                                from crm_lead where crm_lead.date_closed is not null 
                                and crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                      where crm_team.user_id = '%s' and crm_team.id = crm_team_member.crm_team_id 
                                      and crm_team_member.active = true and crm_team.active = true) 
                                AND crm_lead.type = 'opportunity' and crm_lead.active='true' 
                                and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31') 
                                AND Extract(MONTH FROM crm_lead.date_closed) = Extract(MONTH FROM DATE(NOW()))''' % uid)
        else:
            self._cr.execute('''select SUM(COALESCE(crm_lead.expected_revenue, 0)) as expected_revenue
                                from crm_lead where crm_lead.date_closed is not null 
                                AND crm_lead.type = 'opportunity' and crm_lead.active='true' and crm_lead.user_id = '%s'
                                and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31') 
                                AND Extract(MONTH FROM crm_lead.date_closed) = Extract(MONTH FROM DATE(NOW()))''' % uid)
        wons = self._cr.dictfetchall()
        won = [item['expected_revenue'] for item in wons]
        achievement = won[0]
        if achievement is None:
            achievement = 0
        currency_symbol = self.env.company.currency_id.symbol

        goals = []
        if self.env.user.has_group('sales_team.group_sale_manager'):
            self._cr.execute(
                '''select SUM(COALESCE(monthly_goal, 0)) as monthly_goal from crm_team_member WHERE active='true' ''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            self._cr.execute(
                '''select SUM(COALESCE(monthly_goal, 0)) as monthly_goal from crm_team_member   
                    where active='true' and user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                    where crm_team.user_id = '%s' and crm_team.id = crm_team_member.crm_team_id 
                    and crm_team_member.active = true and crm_team.active = true) ''' % uid)
        else:
            self._cr.execute('''select SUM(COALESCE(monthly_goal, 0)) as monthly_goal from crm_team_member 
                                where active='true' and user_id = '%s' ''' % uid)
        monthly_golas = self._cr.dictfetchall()
        golas_ids = [item['monthly_goal'] for item in monthly_golas]
        total = golas_ids[0]
        if total is None:
            total = 0
        self.monthly_goal = total
        self.achievement_amount = achievement

        percent = 0
        if total > 0:
            percent = (achievement * 100 / total) / 100

        goals.append(achievement)
        goals.append(total)
        goals.append(currency_symbol)
        goals.append(percent)

        return {'goals': goals}

    # 查询本月目标与完成（Monthly Goal）
    @api.model
    def search_monthly_goal(self, month, user_id):
        """Monthly Goal Gauge"""
        uid = request.session.uid
        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != '0':
                self._cr.execute('''select SUM(COALESCE(crm_lead.expected_revenue, 0)) as expected_revenue
                                                    from crm_lead where crm_lead.date_closed is not null 
                                                    AND crm_lead.type = 'opportunity' and crm_lead.active='true' and crm_lead.user_id = %s
                                                    and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31') 
                                                    AND Extract(MONTH FROM crm_lead.date_closed) = %s''', (user_id, month))
            else:
                self._cr.execute('''select SUM(COALESCE(crm_lead.expected_revenue, 0)) as expected_revenue
                                                    from crm_lead where crm_lead.date_closed is not null 
                                                    AND crm_lead.type = 'opportunity' and crm_lead.active='true' 
                                                    and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31') 
                                                    AND Extract(MONTH FROM crm_lead.date_closed) = %s''' % month)
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != '0':
                self._cr.execute('''select SUM(COALESCE(crm_lead.expected_revenue, 0)) as expected_revenue
                                                    from crm_lead where crm_lead.date_closed is not null 
                                                    AND crm_lead.type = 'opportunity' and crm_lead.active='true' and crm_lead.user_id = %s
                                                    and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31') 
                                                    AND Extract(MONTH FROM crm_lead.date_closed) = %s''', (user_id, month))
            else:
                self._cr.execute('''select SUM(COALESCE(crm_lead.expected_revenue, 0)) as expected_revenue
                                                    from crm_lead where crm_lead.date_closed is not null 
                                                    and crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                                          where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                          and crm_team_member.active = true and crm_team.active = true) 
                                                    AND crm_lead.type = 'opportunity' and crm_lead.active='true' 
                                                    and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31') 
                                                    AND Extract(MONTH FROM crm_lead.date_closed) = %s''', (uid, month))
        else:
            self._cr.execute('''select SUM(COALESCE(crm_lead.expected_revenue, 0)) as expected_revenue
                                    from crm_lead where crm_lead.date_closed is not null 
                                    AND crm_lead.type = 'opportunity' and crm_lead.active='true' and crm_lead.user_id = %s
                                    and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31') 
                                    AND Extract(MONTH FROM crm_lead.date_closed) = %s''', (uid, month))
        wons = self._cr.dictfetchall()
        won = [item['expected_revenue'] for item in wons]
        achievement = won[0]
        if achievement is None:
            achievement = 0
        currency_symbol = self.env.company.currency_id.symbol

        goals = []
        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != '0':
                self._cr.execute('''select SUM(COALESCE(monthly_goal, 0)) as monthly_goal from crm_team_member 
                where crm_team_member.active = true and user_id = %s ''' % user_id)
            else:
                self._cr.execute('''select SUM(COALESCE(monthly_goal, 0)) as monthly_goal from crm_team_member 
                    where crm_team_member.active = true''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != '0':
                self._cr.execute('''select SUM(COALESCE(monthly_goal, 0)) as monthly_goal from crm_team_member 
                where crm_team_member.active = true and user_id = %s ''' % user_id)
            else:
                self._cr.execute('''select SUM(COALESCE(monthly_goal, 0)) as monthly_goal from crm_team_member 
                                        where crm_team_member.active = true and user_id in 
                                        (select crm_team_member.user_id from crm_team_member, crm_team 
                                            where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                            and crm_team_member.active = true and crm_team.active = true) ''' % uid)
        else:
            self._cr.execute(
                '''select SUM(COALESCE(monthly_goal, 0)) as monthly_goal from crm_team_member where user_id = %s ''' % uid)
        monthly_golas = self._cr.dictfetchall()
        golas_ids = [item['monthly_goal'] for item in monthly_golas]
        total = golas_ids[0]
        if total is None:
            total = 0
        self.monthly_goal = total
        self.achievement_amount = achievement

        percent = 0
        if total > 0:
            percent = (achievement * 100 / total) / 100

        goals.append(achievement)
        goals.append(total)
        goals.append(currency_symbol)
        goals.append(percent)

        return {'goals': goals}

    # 初始化本季度目标与完成（Quarter Goal）
    @api.model
    def get_quarter_goal(self):
        """Quarter Goal Gauge"""
        uid = request.session.uid
        # 当前月
        current_month = int(time.strftime('%m', time.localtime(time.time())))
        month_one = 1
        month_two = 1
        month_three = 1
        if current_month < 4:
            month_one = 1
            month_two = 2
            month_three = 3
        elif current_month < 7:
            month_one = 4
            month_two = 5
            month_three = 6
        elif current_month < 10:
            month_one = 7
            month_two = 8
            month_three = 9
        else:
            month_one = 10
            month_two = 11
            month_three = 12

        if self.env.user.has_group('sales_team.group_sale_manager'):
            self._cr.execute('''select SUM(COALESCE(crm_lead.expected_revenue, 0)) as expected_revenue
                                    from crm_lead where crm_lead.date_closed is not null 
                                    AND crm_lead.type = 'opportunity' and crm_lead.active='true' 
                                    and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31') 
                                    AND Extract(MONTH FROM crm_lead.date_closed) in (%s, %s, %s)''', (month_one, month_two, month_three) )
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            self._cr.execute('''select SUM(COALESCE(crm_lead.expected_revenue, 0)) as expected_revenue
                                    from crm_lead where crm_lead.date_closed is not null 
                                    and crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                          where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                          and crm_team_member.active = true and crm_team.active = true) 
                                    AND crm_lead.type = 'opportunity' and crm_lead.active='true' 
                                    and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31') 
                                    AND Extract(MONTH FROM crm_lead.date_closed) in (%s, %s, %s)''', (uid, month_one, month_two, month_three))
        else:
            self._cr.execute('''select SUM(COALESCE(crm_lead.expected_revenue, 0)) as expected_revenue
                                    from crm_lead where crm_lead.date_closed is not null 
                                    AND crm_lead.type = 'opportunity' and crm_lead.active='true' and crm_lead.user_id = %s
                                    and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31') 
                                    AND Extract(MONTH FROM crm_lead.date_closed) in (%s, %s, %s)''', (uid, month_one, month_two, month_three))
        wons = self._cr.dictfetchall()
        won = [item['expected_revenue'] for item in wons]
        achievement = won[0]
        if achievement is None:
            achievement = 0
        currency_symbol = self.env.company.currency_id.symbol

        goals = []
        if self.env.user.has_group('sales_team.group_sale_manager'):
            self._cr.execute(
                '''select SUM(COALESCE(monthly_goal, 0)) as monthly_goal from crm_team_member WHERE active=true ''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            self._cr.execute(
                '''select SUM(COALESCE(monthly_goal, 0)) as monthly_goal from crm_team_member   
                    where active='true' and user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                    where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                    and crm_team_member.active = true and crm_team.active = true) ''' % uid)
        else:
            self._cr.execute('''select SUM(COALESCE(monthly_goal, 0)) as monthly_goal from crm_team_member 
                                where active='true' and user_id = %s ''' % uid)
        monthly_golas = self._cr.dictfetchall()
        golas_ids = [item['monthly_goal'] for item in monthly_golas]
        total = golas_ids[0]
        if total is None:
            total = 0
        else:
            total = total * 3
        self.monthly_goal = total
        self.achievement_amount = achievement

        percent = 0
        if total > 0:
            percent = (achievement * 100 / total) / 100

        goals.append(achievement)
        goals.append(total)
        goals.append(currency_symbol)
        goals.append(percent)

        return {'quarter_goals': goals}

    # 查询本季度目标与完成（Quarter Goal）
    @api.model
    def search_quarter_goal(self, quarter, user_id):
        """Quarter Goal Gauge"""
        uid = request.session.uid
        if quarter == '1':
            month_one = 1
            month_two = 2
            month_three = 3
        elif quarter == '2':
            month_one = 4
            month_two = 5
            month_three = 6
        elif quarter == '3':
            month_one = 7
            month_two = 8
            month_three = 9
        else:
            month_one = 10
            month_two = 11
            month_three = 12
        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != '0':
                self._cr.execute('''select SUM(COALESCE(crm_lead.expected_revenue, 0)) as expected_revenue
                                                        from crm_lead where crm_lead.date_closed is not null 
                                                        AND crm_lead.type = 'opportunity' and crm_lead.active='true' and crm_lead.user_id = %s
                                                        and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31') 
                                                        AND Extract(MONTH FROM crm_lead.date_closed) in (%s, %s, %s)''',
                                 (user_id, month_one, month_two, month_three))
            else:
                self._cr.execute('''select SUM(COALESCE(crm_lead.expected_revenue, 0)) as expected_revenue
                                                        from crm_lead where crm_lead.date_closed is not null 
                                                        AND crm_lead.type = 'opportunity' and crm_lead.active='true' 
                                                        and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31') 
                                                        AND Extract(MONTH FROM crm_lead.date_closed) in (%s, %s, %s)''', (month_one, month_two, month_three))
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != '0':
                self._cr.execute('''select SUM(COALESCE(crm_lead.expected_revenue, 0)) as expected_revenue
                                                        from crm_lead where crm_lead.date_closed is not null 
                                                        AND crm_lead.type = 'opportunity' and crm_lead.active='true' and crm_lead.user_id = %s
                                                        and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31') 
                                                        AND Extract(MONTH FROM crm_lead.date_closed) in (%s, %s, %s)''', (user_id, month_one, month_two, month_three))
            else:
                self._cr.execute('''select SUM(COALESCE(crm_lead.expected_revenue, 0)) as expected_revenue
                                                        from crm_lead where crm_lead.date_closed is not null 
                                                        and crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                                              where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                              and crm_team_member.active = true and crm_team.active = true) 
                                                        AND crm_lead.type = 'opportunity' and crm_lead.active='true' 
                                                        and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31') 
                                                        AND Extract(MONTH FROM crm_lead.date_closed) in (%s, %s, %s)''', (uid, month_one, month_two, month_three))
        else:
            self._cr.execute('''select SUM(COALESCE(crm_lead.expected_revenue, 0)) as expected_revenue
                                        from crm_lead where crm_lead.date_closed is not null 
                                        AND crm_lead.type = 'opportunity' and crm_lead.active='true' and crm_lead.user_id = %s
                                        and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31') 
                                        AND Extract(MONTH FROM crm_lead.date_closed) in (%s, %s, %s)''', (uid, month_one, month_two, month_three))
        wons = self._cr.dictfetchall()
        won = [item['expected_revenue'] for item in wons]
        achievement = won[0]
        if achievement is None:
            achievement = 0
        currency_symbol = self.env.company.currency_id.symbol

        goals = []
        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != '0':
                self._cr.execute('''select SUM(COALESCE(monthly_goal, 0)) as monthly_goal from crm_team_member 
                    where crm_team_member.active = true and user_id = %s ''' % user_id)
            else:
                self._cr.execute('''select SUM(COALESCE(monthly_goal, 0)) as monthly_goal from crm_team_member 
                        where crm_team_member.active = true''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != '0':
                self._cr.execute('''select SUM(COALESCE(monthly_goal, 0)) as monthly_goal from crm_team_member 
                    where crm_team_member.active = true and user_id = %s ''' % user_id)
            else:
                self._cr.execute('''select SUM(COALESCE(monthly_goal, 0)) as monthly_goal from crm_team_member 
                                            where crm_team_member.active = true and user_id in 
                                            (select crm_team_member.user_id from crm_team_member, crm_team 
                                                where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                and crm_team_member.active = true and crm_team.active = true) ''' % uid)
        else:
            self._cr.execute(
                '''select SUM(COALESCE(monthly_goal, 0)) as monthly_goal from crm_team_member where user_id = %s ''' % uid)
        monthly_golas = self._cr.dictfetchall()
        golas_ids = [item['monthly_goal'] for item in monthly_golas]
        total = golas_ids[0]
        if total is None:
            total = 0
        else:
            total = total * 3
        self.monthly_goal = total
        self.achievement_amount = achievement

        percent = 0
        if total > 0:
            percent = (achievement * 100 / total) / 100

        goals.append(achievement)
        goals.append(total)
        goals.append(currency_symbol)
        goals.append(percent)

        return {'goals': goals}

    # 初始化本年目标与完成（Year Goal）
    @api.model
    def get_year_goal(self):
        """Year Goal Gauge"""
        uid = request.session.uid
        # 当前月
        current_year = int(time.strftime('%Y', time.localtime(time.time())))

        if self.env.user.has_group('sales_team.group_sale_manager'):
            self._cr.execute('''select SUM(COALESCE(crm_lead.expected_revenue, 0)) as expected_revenue
                                        from crm_lead where crm_lead.date_closed is not null 
                                        AND crm_lead.type = 'opportunity' and crm_lead.active='true' 
                                        and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31') 
                                        AND Extract(YEAR FROM crm_lead.date_closed) = %s ''' % current_year)
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            self._cr.execute('''select SUM(COALESCE(crm_lead.expected_revenue, 0)) as expected_revenue
                                        from crm_lead where crm_lead.date_closed is not null 
                                        and crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                              where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                              and crm_team_member.active = true and crm_team.active = true) 
                                        AND crm_lead.type = 'opportunity' and crm_lead.active='true' 
                                        and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31') 
                                        AND Extract(YEAR FROM crm_lead.date_closed) = %s ''',
                             (uid, current_year))
        else:
            self._cr.execute('''select SUM(COALESCE(crm_lead.expected_revenue, 0)) as expected_revenue
                                        from crm_lead where crm_lead.date_closed is not null 
                                        AND crm_lead.type = 'opportunity' and crm_lead.active='true' and crm_lead.user_id = %s
                                        and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31') 
                                        AND Extract(YEAR FROM crm_lead.date_closed) = %s ''',
                             (uid, current_year))
        wons = self._cr.dictfetchall()
        won = [item['expected_revenue'] for item in wons]
        achievement = won[0]
        if achievement is None:
            achievement = 0
        currency_symbol = self.env.company.currency_id.symbol

        goals = []
        if self.env.user.has_group('sales_team.group_sale_manager'):
            self._cr.execute(
                '''select SUM(COALESCE(monthly_goal, 0)) as monthly_goal from crm_team_member WHERE active='true' ''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            self._cr.execute(
                '''select SUM(COALESCE(monthly_goal, 0)) as monthly_goal from crm_team_member   
                    where active='true' and user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                    where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                    and crm_team_member.active = true and crm_team.active = true) ''' % uid)
        else:
            self._cr.execute('''select SUM(COALESCE(monthly_goal, 0)) as monthly_goal from crm_team_member 
                                    where active='true' and user_id = %s ''' % uid)
        monthly_golas = self._cr.dictfetchall()
        golas_ids = [item['monthly_goal'] for item in monthly_golas]
        total = golas_ids[0]
        if total is None:
            total = 0
        else:
            total = total * 12
        self.monthly_goal = total
        self.achievement_amount = achievement
        percent = 0
        if total > 0:
            percent = (achievement * 100 / total) / 100
        goals.append(achievement)
        goals.append(total)
        goals.append(currency_symbol)
        goals.append(percent)
        return {'quarter_goals': goals}

    # 查询本年目标与完成（Year Goal）
    @api.model
    def search_year_goal(self, year, user_id):
        """Year Goal Gauge"""
        uid = request.session.uid
        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != '0':
                self._cr.execute('''select SUM(COALESCE(crm_lead.expected_revenue, 0)) as expected_revenue
                                                            from crm_lead where crm_lead.date_closed is not null 
                                                            AND crm_lead.type = 'opportunity' and crm_lead.active='true' and crm_lead.user_id = %s
                                                            and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31') 
                                                            AND Extract(YEAR FROM crm_lead.date_closed) = %s ''',
                                 (user_id, year))
            else:
                self._cr.execute('''select SUM(COALESCE(crm_lead.expected_revenue, 0)) as expected_revenue
                                                            from crm_lead where crm_lead.date_closed is not null 
                                                            AND crm_lead.type = 'opportunity' and crm_lead.active='true' 
                                                            and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31') 
                                                            AND Extract(YEAR FROM crm_lead.date_closed) =%s ''' % year)
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != '0':
                self._cr.execute('''select SUM(COALESCE(crm_lead.expected_revenue, 0)) as expected_revenue
                                                            from crm_lead where crm_lead.date_closed is not null 
                                                            AND crm_lead.type = 'opportunity' and crm_lead.active='true' and crm_lead.user_id = %s
                                                            and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31') 
                                                            AND Extract(YEAR FROM crm_lead.date_closed) = %s ''',
                                 (user_id, year))
            else:
                self._cr.execute('''select SUM(COALESCE(crm_lead.expected_revenue, 0)) as expected_revenue
                                                            from crm_lead where crm_lead.date_closed is not null 
                                                            and crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                                                  where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                                  and crm_team_member.active = true and crm_team.active = true) 
                                                            AND crm_lead.type = 'opportunity' and crm_lead.active='true' 
                                                            and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31') 
                                                            AND Extract(YEAR FROM crm_lead.date_closed) = %s ''',
                                 (uid, year))
        else:
            self._cr.execute('''select SUM(COALESCE(crm_lead.expected_revenue, 0)) as expected_revenue
                                            from crm_lead where crm_lead.date_closed is not null 
                                            AND crm_lead.type = 'opportunity' and crm_lead.active='true' and crm_lead.user_id = %s
                                            and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31') 
                                            AND Extract(YEAR FROM crm_lead.date_closed) in %s ''',
                             (uid, year))
        wons = self._cr.dictfetchall()
        won = [item['expected_revenue'] for item in wons]
        achievement = won[0]
        if achievement is None:
            achievement = 0
        currency_symbol = self.env.company.currency_id.symbol

        goals = []
        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != '0':
                self._cr.execute('''select SUM(COALESCE(monthly_goal, 0)) as monthly_goal from crm_team_member 
                        where crm_team_member.active = true and user_id = %s ''' % user_id)
            else:
                self._cr.execute('''select SUM(COALESCE(monthly_goal, 0)) as monthly_goal from crm_team_member 
                            where crm_team_member.active = true''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != '0':
                self._cr.execute('''select SUM(COALESCE(monthly_goal, 0)) as monthly_goal from crm_team_member 
                        where crm_team_member.active = true and user_id = %s ''' % user_id)
            else:
                self._cr.execute('''select SUM(COALESCE(monthly_goal, 0)) as monthly_goal from crm_team_member 
                                                where crm_team_member.active = true and user_id in 
                                                (select crm_team_member.user_id from crm_team_member, crm_team 
                                                    where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                    and crm_team_member.active = true and crm_team.active = true) ''' % uid)
        else:
            self._cr.execute(
                '''select SUM(COALESCE(monthly_goal, 0)) as monthly_goal from crm_team_member where user_id = %s ''' % uid)
        monthly_golas = self._cr.dictfetchall()
        golas_ids = [item['monthly_goal'] for item in monthly_golas]
        total = golas_ids[0]
        if total is None:
            total = 0
        else:
            total = total * 12
        self.monthly_goal = total
        self.achievement_amount = achievement
        percent = 0
        if total > 0:
            percent = (achievement * 100 / total) / 100
        goals.append(achievement)
        goals.append(total)
        goals.append(currency_symbol)
        goals.append(percent)
        return {'goals': goals}

    @api.model
    def get_top_sp_revenue(self):
        """Top 10 Salesperson revenue Table"""
        user = self.env.user

        self._cr.execute('''SELECT user_id,id,expected_revenue,name,company_id
        from crm_lead where expected_revenue is not null AND user_id = %s
        GROUP BY user_id,id order by expected_revenue DESC limit 10''' % user.id)
        data1 = self._cr.fetchall()

        top_revenue = []
        for rec in data1:
            company_id = rec[4]
            user_id = rec[0]
            company_id_obj = self.env['res.company'].browse(company_id)
            user_id_obj = self.env['res.users'].browse(user_id)
            currency = company_id_obj.currency_id.symbol
            rec_list = list(rec)
            rec_list[0] = user_id_obj.name
            rec_list.append(currency)
            top_revenue.append(rec_list)

        return {'top_revenue': top_revenue}

    @api.model
    def get_country_revenue(self):
        """Top 10 Country Wise Revenue - Heat Map"""
        company_id = self.env.company.id
        self._cr.execute('''select country_id, sum(expected_revenue) from crm_lead
            where expected_revenue is not null AND country_id is not null
            group by country_id order by sum(expected_revenue) desc limit 10''')
        data1 = self._cr.fetchall()

        country_revenue = []
        for rec in data1:
            country_id = rec[0]
            company_id_obj = self.env['res.company'].browse(company_id)
            country_id_obj = self.env['res.country'].browse(country_id)
            currency = company_id_obj.currency_id.symbol
            rec_list = list(rec)
            rec_list[0] = country_id_obj.name
            rec_list.append(currency)
            country_revenue.append(rec_list)

        return {'country_revenue': country_revenue}

    @api.model
    def get_country_count(self):
        """Top 10 Country Wise Count - Heat Map"""
        self._cr.execute('''select country_id,count(*) from crm_lead where country_id is not null
        group by country_id order by count(*) desc limit 10''')
        data1 = self._cr.fetchall()

        country_count = []
        for rec in data1:
            country_id = rec[0]
            country_id_obj = self.env['res.country'].browse(country_id)
            rec_list = list(rec)
            rec_list[0] = country_id_obj.name
            country_count.append(rec_list)

        return {'country_count': country_count}

    @api.model
    def get_total_lost_crm(self, option):
        """Lost Opportunity or Lead Graph"""
        month_dict = {}
        for i in range(int(option) - 1, -1, -1):
            last_month = datetime.now() - relativedelta(months=i)
            text = format(last_month, '%B')
            month_dict[text] = 0

        if option == '1':
            day_dict = {}
            last_day = date_utils.end_of(fields.Date.today(), "month").strftime("%d")

            for i in range(1, int(last_day), 1):
                day_dict[i] = 0

            self._cr.execute('''select create_date::date,count(id) from crm_lead
            where probability=0 and active=false and create_date between (now() - interval '1 month') and now()
            group by create_date order by create_date;''')
            data = self._cr.dictfetchall()

            for rec in data:
                day_dict[int(rec['create_date'].strftime("%d"))] = rec['count']

            test = {'month': list(day_dict.keys()),
                    'count': list(day_dict.values())}
        else:
            month_string = str(int(option)) + ' Months'
            self._cr.execute('''select extract(month from create_date),count(id)
            from crm_lead where probability=0 and active=false and
            create_date between (now() - interval '%s') and now()
            group by extract(month from create_date) order by extract(
            month from create_date);''' % month_string)
            data = self._cr.dictfetchall()

            for rec in data:
                if 'date_part' in rec:
                    datetime_object = datetime.strptime(str(int(rec['date_part'])), "%m")
                    month_name = datetime_object.strftime("%B")
                    month_dict[month_name] = rec['count']

            test = {'month': list(month_dict.keys()),
                    'count': list(month_dict.values())}

        return test

    # @api.model
    # def get_lost_reason_count(self):
    #     """Top 5 Lost Reason and Count"""
    #     self._cr.execute('''select lost_reason_id,count(lost_reason_id) as counts
    #     from crm_lead where probability=0 and active=false and lost_reason_id is not null
    #     group by lost_reason_id order by counts desc limit 5''')
    #     data1 = self._cr.fetchall()
    #
    #     reason_count = []
    #     for rec in data1:
    #         reason_id = rec[0]
    #         reason_id_obj = self.env['crm.lost.reason'].browse(reason_id)
    #         rec_list = list(rec)
    #         rec_list[0] = reason_id_obj.name
    #         reason_count.append(rec_list)
    #
    #     return {'reason_count': reason_count}

    @api.model
    def get_ratio_based_country(self):
        """Top 5 Won vs Lost Ratio based on Country"""
        self._cr.execute('''select (select name from res_country where id=country_id),
        count(country_id) from crm_lead where probability=100 and active=true
        group by country_id order by count(country_id) desc''')
        data_won = self._cr.fetchall()

        self._cr.execute('''select (select name from res_country where id=country_id),
        count(country_id) from crm_lead where probability=0 and active=false
        group by country_id order by count(country_id) desc''')
        data_lost = self._cr.fetchall()

        won = []
        for rec in data_won:
            won_list = list(rec)
            won.append(won_list)

            for lose in data_lost:
                lose_list = list(lose)

                if lose_list[0] == won_list[0]:
                    won_list.append(lose_list[1])

        country_wise_ratio = []
        for data in won:
            if len(data) != 3:
                del data
            else:
                if data[2] == 0:
                    ratio = 0
                else:
                    ratio = round(data[1] / data[2], 2)
                data.append(str(ratio))
                country_wise_ratio.append(data)

        country_wise_ratio = sorted(country_wise_ratio, key=lambda x: x[3], reverse=True)
        country_wise_ratio = country_wise_ratio[:5]

        return {'country_wise_ratio': country_wise_ratio}

    @api.model
    def get_ratio_based_sp(self):
        """Top 5 Won vs Lost Ratio based on Sales Person"""
        self._cr.execute('''select user_id,count(user_id) from crm_lead where
        probability=100 and active=true group by user_id order by count(user_id) desc''')
        data_won = self._cr.fetchall()

        self._cr.execute('''select user_id,count(user_id) from crm_lead where probability=0
        and active=false group by user_id order by count(user_id) desc''')
        data_lost = self._cr.fetchall()

        won = []
        for rec in data_won:
            won_list = list(rec)
            user_id = rec[0]
            user_id_obj = self.env['res.users'].browse(user_id)
            won_list[0] = user_id_obj.name
            won.append(won_list)

            for lose in data_lost:
                lose_list = list(lose)
                user_id = lose[0]
                user_id_obj = self.env['res.users'].browse(user_id)
                lose_list[0] = user_id_obj.name

                if lose_list[0] == won_list[0]:
                    won_list.append(lose_list[1])

        salesperson_wise_ratio = []
        for data in won:
            if len(data) != 3:
                del data
            else:
                if data[2] == 0:
                    ratio = 0
                else:
                    ratio = round(data[1] / data[2], 2)
                data.append(str(ratio))
                salesperson_wise_ratio.append(data)

        salesperson_wise_ratio = sorted(salesperson_wise_ratio, key=lambda x: x[3], reverse=True)
        salesperson_wise_ratio = salesperson_wise_ratio[:5]

        return {'salesperson_wise_ratio': salesperson_wise_ratio}

    @api.model
    def get_ratio_based_sales_team(self):
        """Top 5 Won vs Lost Ratio based on Sales Team"""
        self._cr.execute('''select (SELECT name FROM crm_team WHERE crm_team.id = team_id),
        count(user_id) from crm_lead where probability=100 and active=true
        group by team_id order by count(team_id) desc''')
        data_won = self._cr.fetchall()

        self._cr.execute('''select (SELECT name FROM crm_team WHERE crm_team.id = team_id),
        count(user_id) from crm_lead where probability=0 and active=false
        group by team_id order by count(team_id) desc''')
        data_lost = self._cr.fetchall()

        won = []
        for rec in data_won:
            won_list = list(rec)
            won.append(won_list)

            for lose in data_lost:
                lose_list = list(lose)

                if lose_list[0] == won_list[0]:
                    won_list.append(lose_list[1])

        sales_team_wise_ratio = []
        for data in won:
            if len(data) != 3:
                del data
            else:
                if data[2] == 0:
                    ratio = 0
                else:
                    ratio = round(data[1] / data[2], 2)
                data.append(str(ratio))
                sales_team_wise_ratio.append(data)

        sales_team_wise_ratio = sorted(sales_team_wise_ratio, key=lambda x: x[3], reverse=True)
        sales_team_wise_ratio = sales_team_wise_ratio[:5]

        return {'sales_team_wise_ratio': sales_team_wise_ratio}

    @api.model
    def get_lost_lead_by_reason_pie(self):
        """Lost Leads by Lost Reason Pie"""
        self._cr.execute('''select lost_reason, count(*), (SELECT name FROM crm_lost_reason
        WHERE id = lost_reason) from crm_lead where probability=0 and active=false and
        type='lead' group by lost_reason''')
        data1 = self._cr.dictfetchall()

        name = []
        for rec in data1:
            if rec["name"] is None:
                rec["name"] = "Undefined"
            name.append(rec.get('name'))

        count = []
        for rec in data1:
            count.append(rec.get('count'))

        lost_leads = [count, name]
        return lost_leads

    @api.model
    def get_lost_lead_by_stage_pie(self):
        """Lost Leads by Stage Pie"""
        self._cr.execute('''select stage_id, count(*),(SELECT name FROM crm_stage
        WHERE id = stage_id) from crm_lead where probability=0 and active=false
        and type='lead' group by stage_id''')
        data1 = self._cr.dictfetchall()

        name = []
        for rec in data1:
            name.append(rec.get('name'))

        count = []
        for rec in data1:
            count.append(rec.get('count'))

        lost_leads_stage = [count, name]
        return lost_leads_stage

    @api.model
    def get_recent_activities(self):
        """Recent Activities Table"""
        today = fields.date.today()
        recent_week = today - relativedelta(days=7)
        self._cr.execute('''select mail_activity.activity_type_id,mail_activity.date_deadline,
        mail_activity.summary,mail_activity.res_name,(SELECT mail_activity_type.name
        FROM mail_activity_type WHERE mail_activity_type.id = mail_activity.activity_type_id),
        mail_activity.user_id FROM mail_activity WHERE res_model = 'crm.lead' AND
        mail_activity.date_deadline between '%s' and '%s' GROUP BY mail_activity.activity_type_id,
        mail_activity.date_deadline,mail_activity.summary,mail_activity.res_name,mail_activity.user_id
        order by mail_activity.date_deadline desc''' % (recent_week, today))
        data = self._cr.fetchall()
        activities = []
        for record in data:
            user_id = record[5]
            user_id_obj = self.env['res.users'].browse(user_id)
            record_list = list(record)
            record_list[5] = user_id_obj.name
            activities.append(record_list)

        return {'activities': activities}

    @api.model
    def get_count_unassigned(self):
        """Unassigned Leads Count Card"""
        count_unassigned = self.env['crm.lead'].search_count(
            [('user_id', '=', False), ('type', '=', 'lead')])

        return {'count_unassigned': count_unassigned}

    @api.model
    def get_top_sp_by_invoice(self):
        """Top 10 Sales Person by Invoice Table"""
        self._cr.execute('''select user_id,sum(amount_total) as total
        from sale_order where invoice_status='invoiced'
        group by user_id order by total desc limit 10''')
        data1 = self._cr.fetchall()

        sales_person_invoice = []
        num = 0
        for rec in data1:
            user_id = rec[0]
            user_id_obj = self.env['res.users'].browse(user_id)
            currency = user_id_obj.company_id.currency_id.symbol
            rec_list = list(rec)
            rec_list[0] = user_id_obj.name
            num += 1
            rec_list.append(currency)
            rec_list.append(num)
            sales_person_invoice.append(rec_list)

        return {'sales_person_invoice': sales_person_invoice}

    @api.model
    def lead_details_user(self):
        """Cards Count and Details based on User"""
        session_user_id = self.env.uid
        month_count = []
        month_value = []
        leads = self.env['crm.lead'].search([])
        for rec in leads:
            month = rec.create_date.month
            if month not in month_value:
                month_value.append(month)
            month_count.append(month)

        value = []
        for index in range(len(month_value)):
            value = month_count.count(month_value[index])

        self._cr.execute('''SELECT res_users.id,res_users.sales,res_users.sale_team_id,
        (SELECT crm_team.invoiced_target FROM crm_team WHERE crm_team.id = res_users.sale_team_id)
        FROM res_users WHERE res_users.sales is not null and res_users.id=%s
        AND res_users.sale_team_id is not null;''' % session_user_id)
        data2 = self._cr.dictfetchall()

        sales = []
        inv_target = []
        team_id = 0
        for rec in data2:
            sales.append(rec['sales'])
            inv_target.append(rec['invoiced_target'])
            if inv_target == [None]:
                inv_target = [0]
            team_id = rec['sale_team_id']
        target_annual = (sum(sales) + sum(inv_target))

        if self.env.user.has_group('sales_team.group_sale_manager'):
            self._cr.execute('''SELECT res_users.id,res_users.sales,res_users.sale_team_id,
            (SELECT crm_team.invoiced_target FROM crm_team WHERE
            crm_team.id = res_users.sale_team_id) FROM res_users WHERE res_users.id = %s
            AND res_users.sales is not null;''' % session_user_id)
            data3 = self._cr.dictfetchall()

            sales = []
            inv_target = []
            for rec in data3:
                sales.append(rec['sales'])
                inv_target.append(rec['invoiced_target'])
                if inv_target == [None]:
                    inv_target = [0]
            ytd_target = (sum(sales) + sum(inv_target))

            self._cr.execute('''select sum(expected_revenue) from crm_lead where stage_id=4
            and team_id=%s AND Extract(Year FROM date_closed)=Extract(Year FROM DATE(NOW(
            )))''' % team_id)
            achieved_won_data = self._cr.dictfetchall()
            achieved_won = [item['sum'] for item in achieved_won_data]

        else:
            self._cr.execute('''SELECT res_users.id,res_users.sales FROM res_users
            WHERE res_users.id = %s AND res_users.sales is not null;''' % session_user_id)
            data4 = self._cr.dictfetchall()

            sales = []
            for rec in data4:
                sales.append(rec['sales'])
            ytd_target = (sum(sales))

            self._cr.execute('''select sum(expected_revenue) from crm_lead where stage_id=4
            and user_id=%s AND Extract(Year FROM date_closed)=Extract(Year FROM DATE(NOW(
            )))''' % session_user_id)
            achieved_won_data = self._cr.dictfetchall()
            achieved_won = [item['sum'] for item in achieved_won_data]

        won = achieved_won[0]
        if won is None:
            won = 0
        difference = target_annual - won

        if self.env.user.has_group('sales_team.group_sale_manager'):
            self._cr.execute('''select COUNT(id) from res_partner where type != 'private' and active = true  
            and partner_share = true''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            self._cr.execute('''select COUNT(id) from res_partner where type != 'private' and active = true  
                                    and (user_id is null  or user_id = '%s'
                                            or (res_partner.user_id in 
	                                                (select crm_team_member.user_id from crm_team_member, crm_team 
                                                        where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                        and crm_team_member.active = true and crm_team.active = true))
	                                    )
                                and partner_share = true
                        ''', (session_user_id, session_user_id))
        else:
            self._cr.execute('''select COUNT(id) from res_partner where type != 'private' and partner_share = true 
                                and active = true and (user_id = %s or user_id is null) ''' % session_user_id)
        customer = self._cr.dictfetchall()
        customer_ids = [item['count'] for item in customer]
        customer_value = customer_ids[0]

        if self.env.user.has_group('sales_team.group_sale_manager'):
            self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.type='lead' AND
                                        Extract(MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW()))
                                        AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.type='lead' AND (
                                  (crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                    where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                    and crm_team_member.active = true and crm_team.active = true))
        			              OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
        			              OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team where crm_team.user_id = %s))
        			              ) 
                        AND Extract(MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW()))
                        AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                        ''', (session_user_id, session_user_id))
        else:
            self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.type='lead' 
                            AND (crm_lead.user_id = %s or crm_lead.user_id is null) 
                            AND Extract(MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW()))
                            AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                            ''' % session_user_id)
        record = self._cr.dictfetchall()
        rec_ids = [item['count'] for item in record]
        crm_lead_value = rec_ids[0]

        if self.env.user.has_group('sales_team.group_sale_manager'):
            self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true
                                        AND crm_lead.type = 'opportunity' AND Extract(MONTH FROM crm_lead.date_deadline
                                        ) = Extract(MONTH FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_deadline
                                        ) = Extract(Year FROM DATE(NOW( )))
                                        and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and (
                                        (crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                            where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                            and crm_team_member.active = true and crm_team.active = true))
        			                    OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
        			                    OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team where crm_team.user_id = %s))
        			                    )
                                        AND crm_lead.type = 'opportunity' AND Extract(MONTH FROM crm_lead.date_deadline
                                        ) = Extract(MONTH FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_deadline
                                        ) = Extract(Year FROM DATE(NOW( )))
                                        and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')''',
                             (session_user_id, session_user_id))
        else:
            self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.user_id = %s
                            AND crm_lead.type = 'opportunity' AND Extract(MONTH FROM crm_lead.date_deadline
                            ) = Extract(MONTH FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_deadline
                            ) = Extract(Year FROM DATE(NOW( )))
                            and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30','31')
                            ''' % session_user_id)
        opportunity_data = self._cr.dictfetchall()
        opportunity_data_value = [item['count'] for item in opportunity_data]
        opportunity_value = opportunity_data_value[0]

        if self.env.user.has_group('sales_team.group_sale_manager'):
            self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                            type='opportunity' and active='true' AND Extract(
                            MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW())) AND
                            Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                            and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                            ''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                            ((crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                 where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                 and crm_team_member.active = true and crm_team.active = true))
        			          OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
        			          OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team where crm_team.user_id = %s)) )
        			        and type='opportunity' and active='true' AND Extract(
                            MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW())) AND
                            Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                            and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                            ''', (session_user_id, session_user_id))
        else:
            self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                            crm_lead.user_id = %s and type='opportunity' and active='true' AND Extract(
                            MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW())) AND
                            Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                            and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                            ''' % session_user_id)
        exp_revenue_data = self._cr.dictfetchall()
        exp_revenue_data_value = [item['sum'] for item in exp_revenue_data]
        exp_revenue_value = exp_revenue_data_value[0]
        if exp_revenue_value is None:
            exp_revenue_value = 0

        if self.env.user.has_group('sales_team.group_sale_manager'):
            self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE type='opportunity' and active='true' 
                                                and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                                AND Extract(MONTH FROM crm_lead.date_closed) = Extract(MONTH FROM DATE(NOW()))
                                                AND Extract(Year FROM crm_lead.date_closed) = Extract(Year FROM DATE(NOW()))
                                                ''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                                                ((crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                                       where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                       and crm_team_member.active = true and crm_team.active = true))
                			                      OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
                			                      OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team where crm_team.user_id = %s)) )
                                                and type='opportunity' and active='true' 
                                                and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                                AND Extract(MONTH FROM crm_lead.date_closed) = Extract(MONTH FROM DATE(NOW()))
                                                AND Extract(Year FROM crm_lead.date_closed) = Extract(Year FROM DATE(NOW()))
                                                ''', (session_user_id, session_user_id))
        else:
            self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                                    crm_lead.user_id = %s and type='opportunity' and active='true' 
                                    and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                    AND Extract(MONTH FROM crm_lead.date_closed) = Extract(MONTH FROM DATE(NOW()))
                                    AND Extract(Year FROM crm_lead.date_closed) = Extract(Year FROM DATE(NOW()))
                                    ''' % session_user_id)
        revenue_data = self._cr.dictfetchall()
        revenue_data_value = [item['sum'] for item in revenue_data]
        revenue_value = revenue_data_value[0]
        if revenue_value is None:
            revenue_value = 0

        ratio_value = []
        if revenue_value == 0:
            ratio_value = 0
        if revenue_value > 0:
            if self.env.user.has_group('sales_team.group_sale_manager'):
                self._cr.execute('''select case when b.count_two = 0 then 0 else (
                                                        CAST(a.count_one as float) / CAST(b.count_two as float))end as final_count
                                                        from (select COUNT(id) as count_one from crm_lead
                                                        WHERE crm_lead.active = True  AND TYPE ='opportunity' AND crm_lead.probability = 100
                                                        AND Extract(MONTH FROM crm_lead.date_deadline
                                                        ) = Extract(MONTH FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_open
                                                        ) = Extract(Year FROM DATE(NOW())))a,
                                                        (select COUNT(id) as count_two from crm_lead WHERE TYPE ='opportunity'
                                                        AND Extract(MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW()))
                                                        AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW())))b
                                                        ''')
            elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
                self._cr.execute('''select case when b.count_two = 0 then 0 else (
                                                        CAST(a.count_one as float) / CAST(b.count_two as float))end as final_count
                                                        from (select COUNT(id) as count_one from crm_lead
                                                        WHERE ((crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                                                    where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                                    and crm_team_member.active = true and crm_team.active = true))
            			                                        OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
            			                                        OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team where crm_team.user_id = %s)) )
                                                        AND crm_lead.active = True  AND TYPE ='opportunity'
                                                        AND crm_lead.probability = 100 AND Extract(MONTH FROM crm_lead.date_deadline
                                                        ) = Extract(MONTH FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_open
                                                        ) = Extract(Year FROM DATE(NOW())))a,
                                                        (select COUNT(id) as count_two from crm_lead WHERE 
                                                        ((crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                                                where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                                and crm_team_member.active = true and crm_team.active = true))
            			                                  OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
            			                                  OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team where crm_team.user_id = %s)) )
                                                        AND TYPE ='opportunity' AND Extract(
                                                        MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW())) AND
                                                        Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW())))b
                                                        ''' % (
                session_user_id, session_user_id, session_user_id, session_user_id))
            else:
                self._cr.execute('''select case when b.count_two = 0 then 0 else (
                                        CAST(a.count_one as float) / CAST(b.count_two as float))end as final_count
                                        from (select COUNT(id) as count_one from crm_lead
                                        WHERE crm_lead.user_id = %s AND crm_lead.active = True  AND TYPE ='opportunity'
                                        AND crm_lead.probability = 100 AND Extract(MONTH FROM crm_lead.date_deadline
                                        ) = Extract(MONTH FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_open
                                        ) = Extract(Year FROM DATE(NOW())))a,
                                        (select COUNT(id) as count_two from crm_lead WHERE crm_lead.user_id = %s
                                        AND TYPE ='opportunity' AND Extract(
                                        MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW())) AND
                                        Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW())))b
                                        ''' % (session_user_id, session_user_id))
            ratio_data_value = [row[0] for row in self._cr.fetchall()]
            ratio_value = str(ratio_data_value)[1:-1]
            ratio_value = str(round(float(ratio_value) * 100, 2)) + "%"

        self._cr.execute('''SELECT active,count(active) FROM crm_lead where type='opportunity'
        and active = true and probability = 100 and user_id=%s AND Extract(MONTH FROM date_closed
        ) = Extract(MONTH FROM DATE(NOW())) AND Extract(Year FROM date_closed) = Extract(
        Year FROM DATE(NOW())) or type='opportunity' and active = false and probability = 0
        and user_id=%s AND Extract(MONTH FROM date_deadline) = Extract(MONTH FROM DATE(NOW()))
        AND Extract(Year FROM date_deadline) = Extract(Year FROM DATE(NOW())) GROUP BY active
        ''' % (session_user_id, session_user_id))
        record_opportunity = dict(self._cr.fetchall())
        opportunity_ratio_value = 0.0
        if record_opportunity == {}:
            opportunity_ratio_value = 0.0
        else:
            total_opportunity_won = record_opportunity.get(False)
            total_opportunity_lost = record_opportunity.get(True)
            if total_opportunity_won is None:
                total_opportunity_won = 0
            if total_opportunity_lost is None:
                total_opportunity_lost = 0
                opportunity_ratio_value = 0.0
            if total_opportunity_lost > 0:
                opportunity_ratio_value = round(total_opportunity_won / total_opportunity_lost, 2)

        avg = 0
        if crm_lead_value == 1:
            self._cr.execute('''SELECT id, date_conversion, create_date
            FROM crm_lead WHERE date_conversion IS NOT NULL;''')
            data = self._cr.dictfetchall()
            for rec in data:
                date_close = rec['date_conversion']
                date_create = rec['create_date']
                avg = (date_close - date_create).seconds
        if crm_lead_value > 1:
            self._cr.execute('''SELECT id, date_conversion, create_date
            FROM crm_lead WHERE date_conversion IS NOT NULL;''')
            data1 = self._cr.dictfetchall()
            for rec in data1:
                date_close = rec['date_conversion']
                date_create = rec['create_date']
                avg = (date_close - date_create).seconds

        avg_time = 0 if crm_lead_value == 0 else round(avg / crm_lead_value)

        data = {
            'customer': customer_value,
            'record': crm_lead_value,
            'record_op': opportunity_value,
            'record_rev_exp': exp_revenue_value,
            'record_rev': revenue_value,
            'record_ratio': ratio_value,
            'opportunity_ratio_value': str(opportunity_ratio_value),
            'avg_time': avg_time,
            'count': value,
            'target': target_annual,
            'ytd_target': ytd_target,
            'difference': difference,
            'won': won,
        }
        return data

    @api.model
    def crm_year(self, user_id):
        """Year CRM Dropdown Filter"""
        session_user_id = self.env.uid

        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != '0':
                self._cr.execute('''select COUNT(id) from res_partner where type != 'private' and active = true  
                                        and partner_share = true and user_id = %s ''' % user_id)
            else:
                self._cr.execute('''select COUNT(id) from res_partner where type != 'private' and active = true 
                                                and partner_share = true ''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != '0':
                self._cr.execute('''select COUNT(id) from res_partner where type != 'private' and active = true  and partner_share = true
                                                            and user_id = %s
                                                ''' % user_id)
            else:
                self._cr.execute('''select COUNT(id) from res_partner where type != 'private' and active = true  and partner_share = true
                                                            and (user_id = %s
                                                                 or (res_partner.user_id in 
                        	                                          (select crm_team_member.user_id from crm_team_member, crm_team 
                                                                           where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                                           and crm_team_member.active = true and crm_team.active = true))
                        	                                    )
                                                ''', (session_user_id, session_user_id))
        else:
            self._cr.execute('''select COUNT(id) from res_partner where type != 'private' and partner_share = true 
                                and active = true and user_id = %s  ''' % session_user_id)
        customer = self._cr.dictfetchall()
        customer_ids = [item['count'] for item in customer]
        customer_value = customer_ids[0]

        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != '0':
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.type='lead' 
                                    AND (crm_lead.user_id = %s or crm_lead.user_id is null) 
                                    AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                                    ''' % user_id)
            else:
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.type='lead' AND 
                                                Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != '0':
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.type='lead' 
                                           AND (crm_lead.user_id = %s or crm_lead.user_id is null) 
                                           AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                                 ''' % user_id)
            else:
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.type='lead' AND (
                                          (crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                            where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                            and crm_team_member.active = true and crm_team.active = true))
                			              OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
                			              OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team where crm_team.user_id = %s))
                			              ) 
                                AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                                ''', (session_user_id, session_user_id))
        else:
            self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.type='lead' 
                    AND (crm_lead.user_id = %s or crm_lead.user_id is null) 
                    AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                    ''' % session_user_id)
        record = self._cr.dictfetchall()
        rec_ids = [item['count'] for item in record]
        crm_lead_value = rec_ids[0]

        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != '0':
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.user_id = %s
                                    AND crm_lead.type = 'opportunity' AND Extract(Year FROM crm_lead.date_deadline
                                    ) = Extract(Year FROM DATE(NOW()))
                                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')''' % user_id)
            else:
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true
                                    AND crm_lead.type = 'opportunity' AND Extract(Year FROM crm_lead.date_deadline
                                    ) = Extract(Year FROM DATE(NOW()))
                                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != '0':
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.user_id = %s
                                    AND crm_lead.type = 'opportunity' AND Extract(Year FROM crm_lead.date_deadline
                                    ) = Extract(Year FROM DATE(NOW()))
                                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')''' % user_id)
            else:
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and (
                                                (crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                                    where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                    and crm_team_member.active = true and crm_team.active = true))
                			                    OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
                			                    OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team where crm_team.user_id = %s))
                			                    ) 
                                    AND crm_lead.type = 'opportunity' AND Extract(Year FROM crm_lead.date_deadline
                                    ) = Extract(Year FROM DATE(NOW()))
                                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')''',
                                 (session_user_id, session_user_id))
        else:
            self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.user_id = %s
                    AND crm_lead.type = 'opportunity' AND Extract(Year FROM crm_lead.date_deadline
                    ) = Extract(Year FROM DATE(NOW()))
                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')''' % session_user_id)
        opportunity_data = self._cr.dictfetchall()
        opportunity_data_value = [item['count'] for item in opportunity_data]
        opportunity_value = opportunity_data_value[0]

        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != '0':
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead
                                    WHERE crm_lead.user_id = %s and type='opportunity' and active='true' AND
                                    Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                    ''' % user_id)
            else:
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead
                                                WHERE type='opportunity' and active='true' AND
                                                Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                                                and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                                ''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != '0':
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead
                                    WHERE crm_lead.user_id = %s and type='opportunity' and active='true' AND
                                    Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                    ''' % user_id)
            else:
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead
                                    WHERE ((crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                                where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                and crm_team_member.active = true and crm_team.active = true))
                			                OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
                			                OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team where crm_team.user_id = %s))
                			              )
                			        and type='opportunity' and active=true AND
                                    Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                    ''', (session_user_id, session_user_id))
        else:
            self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead
                    WHERE crm_lead.user_id = %s and type='opportunity' and active='true' AND
                    Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                    ''' % session_user_id)
        exp_revenue_data = self._cr.dictfetchall()
        exp_revenue_data_value = [item['sum'] for item in exp_revenue_data]
        exp_revenue_value = exp_revenue_data_value[0]
        if exp_revenue_value is None:
            exp_revenue_value = 0

        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != '0':
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead
                                    WHERE crm_lead.user_id = %s and type='opportunity' and active='true' 
                                    and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                    AND Extract(Year FROM crm_lead.date_closed) = Extract(Year
                                    FROM DATE(NOW()))''' % user_id)
            else:
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE type='opportunity' and active=true 
                                                and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                                AND Extract(Year FROM crm_lead.date_closed) = Extract(Year FROM DATE(NOW()))''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != '0':
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead
                                    WHERE crm_lead.user_id = %s and type='opportunity' and active='true' 
                                    and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                    AND Extract(Year FROM crm_lead.date_closed) = Extract(Year
                                    FROM DATE(NOW()))''' % user_id)
            else:
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead
                                                WHERE ((crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                                            where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                            and crm_team_member.active = true and crm_team.active = true))
                			                            OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
                			                            OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team where crm_team.user_id = %s))
                			                          )
                			                    and type='opportunity' and active=true 
                                                and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                                AND Extract(Year FROM crm_lead.date_closed) = Extract(Year
                                                FROM DATE(NOW()))''', (session_user_id, session_user_id))
        else:
            self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead
                    WHERE crm_lead.user_id = %s and type='opportunity' and active='true' 
                    and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                    AND Extract(Year FROM crm_lead.date_closed) = Extract(Year
                    FROM DATE(NOW()))''' % session_user_id)

        revenue_data = self._cr.dictfetchall()
        revenue_data_value = [item['sum'] for item in revenue_data]
        revenue_value = revenue_data_value[0]
        if revenue_value is None:
            revenue_value = 0

        ratio_value = []
        if revenue_value == 0:
            ratio_value = 0
        if revenue_value > 0:
            if self.env.user.has_group('sales_team.group_sale_manager'):
                if user_id != '0':
                    self._cr.execute('''select case when b.count_two = 0 then 0 else (
                                                CAST(a.count_one as float) / CAST(b.count_two as float))end as final_count from (
                                                select COUNT(id) as count_one from crm_lead WHERE crm_lead.user_id = %s AND TYPE ='opportunity' 
                                                AND crm_lead.active = True AND crm_lead.probability = 100 AND Extract(Year FROM
                                                crm_lead.date_deadline) = Extract(Year FROM DATE(NOW())))a,
                                                (select COUNT(id) as count_two from crm_lead WHERE crm_lead.user_id = %s
                                                AND TYPE ='opportunity' AND Extract(Year FROM
                                                crm_lead.date_deadline) = Extract(Year FROM DATE(NOW())))b
                                                ''' % (user_id, user_id))
                else:
                    self._cr.execute('''select case when b.count_two = 0 then 0 else (
                                                                CAST(a.count_one as float) / CAST(b.count_two as float))end as final_count from (
                                                                select COUNT(id) as count_one from crm_lead WHERE TYPE ='opportunity' 
                                                                AND crm_lead.active = True AND crm_lead.probability = 100 AND Extract(Year FROM
                                                                crm_lead.date_deadline) = Extract(Year FROM DATE(NOW())))a,
                                                                (select COUNT(id) as count_two from crm_lead WHERE  
                                                                TYPE ='opportunity' AND Extract(Year FROM
                                                                crm_lead.date_deadline) = Extract(Year FROM DATE(NOW())))b
                                                                ''')
            elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
                if user_id != '0':
                    self._cr.execute('''select case when b.count_two = 0 then 0 else (
                                                CAST(a.count_one as float) / CAST(b.count_two as float))end as final_count from (
                                                select COUNT(id) as count_one from crm_lead WHERE crm_lead.user_id = %s AND TYPE ='opportunity' 
                                                AND crm_lead.active = True AND crm_lead.probability = 100 AND Extract(Year FROM
                                                crm_lead.date_deadline) = Extract(Year FROM DATE(NOW())))a,
                                                (select COUNT(id) as count_two from crm_lead WHERE crm_lead.user_id = %s 
                                                AND TYPE ='opportunity' AND Extract(Year FROM
                                                crm_lead.date_deadline) = Extract(Year FROM DATE(NOW())))b
                                                ''', (user_id, user_id))
                else:
                    self._cr.execute('''select case when b.count_two = 0 then 0 else (
                                                                CAST(a.count_one as float) / CAST(b.count_two as float))end as final_count from (
                                                                select COUNT(id) as count_one from crm_lead WHERE 
                                                                ((crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                                                    where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                                    and crm_team_member.active = true and crm_team.active = true))
                    			                                OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
                    			                                OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team where crm_team.user_id = %s))
                    			                                ) 
                                                                AND TYPE ='opportunity' 
                                                                AND crm_lead.active = True AND crm_lead.probability = 100 AND Extract(Year FROM
                                                                crm_lead.date_deadline) = Extract(Year FROM DATE(NOW())))a,
                                                                (select COUNT(id) as count_two from crm_lead WHERE 
                                                                ((crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                                                    where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                                    and crm_team_member.active = true and crm_team.active = true))
                    			                                OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
                    			                                OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team where crm_team.user_id = %s))
                    			                                ) 
                                                                AND TYPE ='opportunity' AND Extract(Year FROM
                                                                crm_lead.date_deadline) = Extract(Year FROM DATE(NOW())))b
                                                                ''', (session_user_id, session_user_id, session_user_id, session_user_id))
            else:
                self._cr.execute('''select case when b.count_two = 0 then 0 else (
                            CAST(a.count_one as float) / CAST(b.count_two as float))end as final_count from (
                            select COUNT(id) as count_one from crm_lead WHERE crm_lead.user_id = %s AND TYPE ='opportunity' 
                            AND crm_lead.active = True AND crm_lead.probability = 100 AND Extract(Year FROM
                            crm_lead.date_deadline) = Extract(Year FROM DATE(NOW())))a,
                            (select COUNT(id) as count_two from crm_lead WHERE crm_lead.user_id = %s 
                            AND TYPE ='opportunity' AND Extract(Year FROM
                            crm_lead.date_deadline) = Extract(Year FROM DATE(NOW())))b
                            ''' % (session_user_id, session_user_id))
            ratio_value = [row[0] for row in self._cr.fetchall()]
            ratio_value = str(ratio_value)[1:-1]
            ratio_value = str(round(float(ratio_value) * 100, 2)) + "%"

        self._cr.execute('''SELECT active,count(active) FROM crm_lead
        where type='opportunity' and active = true and probability = 100 and user_id=%s
        AND Extract(Year FROM date_closed) = Extract(Year FROM DATE(NOW()))
        or type='opportunity' and active = false and probability = 0 and user_id=%s
        AND Extract(Year FROM date_deadline) = Extract(Year FROM DATE(NOW()))
        GROUP BY active''' % (session_user_id, session_user_id))
        record_opportunity = dict(self._cr.fetchall())
        opportunity_ratio_value = 0.0
        if record_opportunity == {}:
            opportunity_ratio_value = 0.0
        else:
            total_opportunity_won = record_opportunity.get(False)
            total_opportunity_lost = record_opportunity.get(True)
            if total_opportunity_won is None:
                total_opportunity_won = 0
            if total_opportunity_lost is None:
                total_opportunity_lost = 0
                opportunity_ratio_value = 0.0
            if total_opportunity_lost > 0:
                opportunity_ratio_value = round(total_opportunity_won / total_opportunity_lost, 2)

        avg = 0
        if crm_lead_value == 1:
            self._cr.execute('''SELECT id, date_conversion, create_date
            FROM crm_lead WHERE date_conversion IS NOT NULL;''')
            data = self._cr.dictfetchall()
            for rec in data:
                date_close = rec['date_conversion']
                date_create = rec['create_date']
                avg = (date_close - date_create).seconds
        if crm_lead_value > 1:
            self._cr.execute('''SELECT id, date_conversion, create_date
            FROM crm_lead WHERE date_conversion IS NOT NULL;''')
            data1 = self._cr.dictfetchall()
            for rec in data1:
                date_close = rec['date_conversion']
                date_create = rec['create_date']
                avg = (date_close - date_create).seconds

        if crm_lead_value == 0:
            record_avg_time = 0
        else:
            record_avg_time = round(avg / crm_lead_value)

        data_year = {
            'customer': customer_value,
            'record': crm_lead_value,
            'record_op': opportunity_value,
            'record_rev_exp': exp_revenue_value,
            'record_rev': revenue_value,
            'record_ratio': ratio_value,
            'opportunity_ratio_value': str(opportunity_ratio_value),
            'avg_time': record_avg_time,
        }
        return data_year

    @api.model
    def crm_quarter(self, user_id):
        """Quarter CRM Dropdown Filter"""
        session_user_id = self.env.uid

        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != '0':
                self._cr.execute('''select COUNT(id) from res_partner where type != 'private' and active = true  
                                        and partner_share = true and user_id = %s ''' % user_id)
            else:
                self._cr.execute('''select COUNT(id) from res_partner where type != 'private' and active = true 
                                                and partner_share = true ''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != '0':
                self._cr.execute('''select COUNT(id) from res_partner where type != 'private' and active = true  and partner_share = true
                                                            and user_id = %s
                                                ''' % user_id)
            else:
                self._cr.execute('''select COUNT(id) from res_partner where type != 'private' and active = true  and partner_share = true
                                                            and (user_id = %s
                                                                 or (res_partner.user_id in 
                        	                                          (select crm_team_member.user_id from crm_team_member, crm_team 
                                                                           where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                                           and crm_team_member.active = true and crm_team.active = true))
                        	                                    )
                                                ''', (session_user_id, session_user_id))
        else:
            self._cr.execute('''select COUNT(id) from res_partner where type != 'private' and partner_share = true 
                                and active = true and user_id = %s  ''' % session_user_id)
        customer = self._cr.dictfetchall()
        customer_ids = [item['count'] for item in customer]
        customer_value = customer_ids[0]
        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != '0':
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.type='lead' 
                                    AND (crm_lead.user_id = %s or crm_lead.user_id is null) 
                                    AND Extract(QUARTER FROM crm_lead.date_deadline) = Extract(QUARTER FROM DATE(NOW()))
                                    AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                                    ''' % user_id)
            else:
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.type='lead' AND 
                                                Extract(QUARTER FROM crm_lead.date_deadline) = Extract(QUARTER FROM DATE(NOW()))
                                                AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != '0':
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.type='lead' 
                                    AND (crm_lead.user_id = %s or crm_lead.user_id is null) 
                                    AND Extract(QUARTER FROM crm_lead.date_deadline) = Extract(QUARTER FROM DATE(NOW()))
                                    AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                                    ''' % user_id)
            else:
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.type='lead' AND (
                                          (crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                            where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                            and crm_team_member.active = true and crm_team.active = true))
                			              OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
                			              OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team where crm_team.user_id = %s))
                			              ) 
                                AND Extract(QUARTER FROM crm_lead.date_deadline) = Extract(QUARTER FROM DATE(NOW()))
                                AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                                ''', (session_user_id, session_user_id))
        else:
            self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.type='lead' 
                    AND (crm_lead.user_id = %s or crm_lead.user_id is null) 
                    AND Extract(QUARTER FROM crm_lead.date_deadline) = Extract(QUARTER FROM DATE(NOW()))
                    AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                    ''' % session_user_id)
        record = self._cr.dictfetchall()
        rec_ids = [item['count'] for item in record]
        crm_lead_value = rec_ids[0]

        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != '0':
                self._cr.execute('''select COUNT(id) from crm_lead  WHERE crm_lead.active = true and crm_lead.user_id = %s
                                    AND crm_lead.type = 'opportunity' AND Extract(QUARTER FROM crm_lead.date_deadline
                                    ) = Extract(QUARTER FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_deadline
                                    ) = Extract(Year FROM DATE(NOW( )))
                                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')''' % user_id)
            else:
                self._cr.execute('''select COUNT(id) from crm_lead  WHERE crm_lead.active = true
                                    AND crm_lead.type = 'opportunity' AND Extract(QUARTER FROM crm_lead.date_deadline
                                    ) = Extract(QUARTER FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_deadline
                                    ) = Extract(Year FROM DATE(NOW( )))
                                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != '0':
                self._cr.execute('''select COUNT(id) from crm_lead  WHERE crm_lead.active = true and crm_lead.user_id = %s
                                    AND crm_lead.type = 'opportunity' AND Extract(QUARTER FROM crm_lead.date_deadline
                                    ) = Extract(QUARTER FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_deadline
                                    ) = Extract(Year FROM DATE(NOW( )))
                                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')''' % user_id)
            else:
                self._cr.execute('''select COUNT(id) from crm_lead  WHERE crm_lead.active = true and (
                                                (crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                                    where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                    and crm_team_member.active = true and crm_team.active = true))
                			                    OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
                			                    OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team where crm_team.user_id = %s))
                			                    ) 
                                    AND crm_lead.type = 'opportunity' AND Extract(QUARTER FROM crm_lead.date_deadline
                                    ) = Extract(QUARTER FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_deadline
                                    ) = Extract(Year FROM DATE(NOW( )))
                                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                    ''', (session_user_id, session_user_id))
        else:
            self._cr.execute('''select COUNT(id) from crm_lead  WHERE crm_lead.active = true and crm_lead.user_id = %s
                    AND crm_lead.type = 'opportunity' AND Extract(QUARTER FROM crm_lead.date_deadline
                    ) = Extract(QUARTER FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_deadline
                    ) = Extract(Year FROM DATE(NOW( )))
                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')''' % session_user_id)
        opportunity_data = self._cr.dictfetchall()
        opportunity_data_value = [item['count'] for item in opportunity_data]
        opportunity_value = opportunity_data_value[0]

        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != '0':
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                                    crm_lead.user_id = %s and type='opportunity' and active='true' AND Extract(
                                    QUARTER FROM crm_lead.date_deadline) = Extract(QUARTER FROM DATE(NOW())) AND
                                    Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                    ''' % user_id)
            else:
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                                                type='opportunity' and active='true' AND Extract(
                                                QUARTER FROM crm_lead.date_deadline) = Extract(QUARTER FROM DATE(NOW())) AND
                                                Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                                                and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                                ''' % session_user_id)
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != '0':
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                                    crm_lead.user_id = %s and type='opportunity' and active='true' AND Extract(
                                    QUARTER FROM crm_lead.date_deadline) = Extract(QUARTER FROM DATE(NOW())) AND
                                    Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                    ''' % user_id)
            else:
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                                                ((crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                                    where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                    and crm_team_member.active = true and crm_team.active = true))
                			                    OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
                			                    OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team where crm_team.user_id = %s))
                			                    ) 
                			                    and type='opportunity' and active='true' AND Extract(
                                                QUARTER FROM crm_lead.date_deadline) = Extract(QUARTER FROM DATE(NOW())) AND
                                                Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                                                and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                                ''', (session_user_id, session_user_id))
        else:
            self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                    crm_lead.user_id = %s and type='opportunity' and active='true' AND Extract(
                    QUARTER FROM crm_lead.date_deadline) = Extract(QUARTER FROM DATE(NOW())) AND
                    Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                    ''' % session_user_id)
        exp_revenue_data = self._cr.dictfetchall()
        exp_revenue_data_value = [item['sum'] for item in exp_revenue_data]
        exp_revenue_value = exp_revenue_data_value[0]
        if exp_revenue_value is None:
            exp_revenue_value = 0

        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != '0':
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                                    crm_lead.user_id = %s and type='opportunity' and active='true' 
                                    and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                    AND Extract(QUARTER FROM crm_lead.date_closed) = Extract(QUARTER FROM
                                    DATE(NOW())) AND Extract(Year FROM crm_lead.date_closed) = Extract(Year
                                    FROM DATE(NOW()))''' % user_id)
            else:
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE type='opportunity' and active='true' 
                                                and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                                AND Extract(QUARTER FROM crm_lead.date_closed) = Extract(QUARTER FROM
                                                DATE(NOW())) AND Extract(Year FROM crm_lead.date_closed) = Extract(Year
                                                FROM DATE(NOW()))''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != '0':
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                                    crm_lead.user_id = %s and type='opportunity' and active='true' 
                                    and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                    AND Extract(QUARTER FROM crm_lead.date_closed) = Extract(QUARTER FROM
                                    DATE(NOW())) AND Extract(Year FROM crm_lead.date_closed) = Extract(Year
                                    FROM DATE(NOW()))''' % user_id)
            else:
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                                                ((crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                                    where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                    and crm_team_member.active = true and crm_team.active = true))
                			                    OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
                			                    OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team where crm_team.user_id = %s))
                			                    )
                                                and type='opportunity' and active='true' 
                                                and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                                AND Extract(QUARTER FROM crm_lead.date_closed) = Extract(QUARTER FROM
                                                DATE(NOW())) AND Extract(Year FROM crm_lead.date_closed) = Extract(Year
                                                FROM DATE(NOW()))''', (session_user_id, session_user_id))
        else:
            self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                    crm_lead.user_id = %s and type='opportunity' and active='true' 
                    and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                    AND Extract(QUARTER FROM crm_lead.date_closed) = Extract(QUARTER FROM
                    DATE(NOW())) AND Extract(Year FROM crm_lead.date_closed) = Extract(Year
                    FROM DATE(NOW()))''' % session_user_id)

        revenue_data = self._cr.dictfetchall()
        revenue_data_value = [item['sum'] for item in revenue_data]
        revenue_value = revenue_data_value[0]
        if revenue_value is None:
            revenue_value = 0

        ratio_value = []
        if revenue_value == 0:
            ratio_value = 0
        if revenue_value > 0:
            if self.env.user.has_group('sales_team.group_sale_manager'):
                if user_id != '0':
                    self._cr.execute('''select case when b.count_two = 0 then 0 else (
                                                CAST(a.count_one as float) / CAST(b.count_two as float))end as final_count
                                                from (select COUNT(id) as count_one from crm_lead 
                                                WHERE crm_lead.user_id = %s AND crm_lead.active = True AND TYPE ='opportunity' AND 
                                                crm_lead.probability = 100 AND Extract(QUARTER FROM crm_lead.date_deadline
                                                ) = Extract(QUARTER FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_open
                                                ) = Extract(Year FROM DATE(NOW())))a,
                                                (select COUNT(id) as count_two from crm_lead WHERE crm_lead.user_id = %s
                                                AND TYPE ='opportunity' AND Extract(
                                                QUARTER FROM crm_lead.date_deadline) = Extract(QUARTER FROM DATE(NOW()))
                                                AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW(
                                                ))))b''' % (user_id, user_id))
                else:
                    self._cr.execute('''select case when b.count_two = 0 then 0 else (
                                                                CAST(a.count_one as float) / CAST(b.count_two as float))end as final_count
                                                                from (select COUNT(id) as count_one from crm_lead 
                                                                WHERE crm_lead.active = True AND TYPE ='opportunity' AND 
                                                                crm_lead.probability = 100 AND Extract(QUARTER FROM crm_lead.date_deadline
                                                                ) = Extract(QUARTER FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_open
                                                                ) = Extract(Year FROM DATE(NOW())))a,
                                                                (select COUNT(id) as count_two from crm_lead WHERE TYPE ='opportunity'
                                                                AND Extract(
                                                                QUARTER FROM crm_lead.date_deadline) = Extract(QUARTER FROM DATE(NOW()))
                                                                AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW(
                                                                ))))b''')
            elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
                if user_id != '0':
                    self._cr.execute('''select case when b.count_two = 0 then 0 else (
                                                CAST(a.count_one as float) / CAST(b.count_two as float))end as final_count
                                                from (select COUNT(id) as count_one from crm_lead 
                                                WHERE crm_lead.user_id = %s AND crm_lead.active = True AND TYPE ='opportunity' AND 
                                                crm_lead.probability = 100 AND Extract(QUARTER FROM crm_lead.date_deadline
                                                ) = Extract(QUARTER FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_open
                                                ) = Extract(Year FROM DATE(NOW())))a,
                                                (select COUNT(id) as count_two from crm_lead WHERE crm_lead.user_id = %s
                                                AND TYPE ='opportunity' AND Extract(
                                                QUARTER FROM crm_lead.date_deadline) = Extract(QUARTER FROM DATE(NOW()))
                                                AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW(
                                                ))))b''' % (user_id, user_id))
                else:
                    self._cr.execute('''select case when b.count_two = 0 then 0 else (
                                                                CAST(a.count_one as float) / CAST(b.count_two as float))end as final_count
                                                                from (select COUNT(id) as count_one from crm_lead 
                                                                WHERE ((crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                                                            where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                                            and crm_team_member.active = true and crm_team.active = true))
                    			                                        OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
                    			                                        OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team where crm_team.user_id = %s))
                    			                                )
                    			                                AND crm_lead.active = True AND TYPE ='opportunity' AND 
                                                                crm_lead.probability = 100 AND Extract(QUARTER FROM crm_lead.date_deadline
                                                                ) = Extract(QUARTER FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_open
                                                                ) = Extract(Year FROM DATE(NOW())))a,
                                                                (select COUNT(id) as count_two from crm_lead WHERE 
                                                                ((crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                                                            where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                                            and crm_team_member.active = true and crm_team.active = true))
                    			                                        OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
                    			                                        OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team where crm_team.user_id = %s))
                    			                                )
                                                                AND TYPE ='opportunity' AND Extract(
                                                                QUARTER FROM crm_lead.date_deadline) = Extract(QUARTER FROM DATE(NOW()))
                                                                AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW(
                                                                ))))b''' % (
                    session_user_id, session_user_id, session_user_id, session_user_id))
            else:
                self._cr.execute('''select case when b.count_two = 0 then 0 else (
                            CAST(a.count_one as float) / CAST(b.count_two as float))end as final_count
                            from (select COUNT(id) as count_one from crm_lead 
                            WHERE crm_lead.user_id = %s AND crm_lead.active = True AND TYPE ='opportunity' AND 
                            crm_lead.probability = 100 AND Extract(QUARTER FROM crm_lead.date_deadline
                            ) = Extract(QUARTER FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_open
                            ) = Extract(Year FROM DATE(NOW())))a,
                            (select COUNT(id) as count_two from crm_lead WHERE crm_lead.user_id = %s
                            AND TYPE ='opportunity' AND Extract(
                            QUARTER FROM crm_lead.date_deadline) = Extract(QUARTER FROM DATE(NOW()))
                            AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW(
                            ))))b''' % (session_user_id, session_user_id))

            ratio_value = [row[0] for row in self._cr.fetchall()]
            ratio_value = str(ratio_value)[1:-1]
            ratio_value = str(round(float(ratio_value) * 100, 2)) + "%"

        self._cr.execute('''SELECT active,count(active) FROM crm_lead
        where type='opportunity' and active = true and probability = 100 and user_id=%s
        AND Extract(QUARTER FROM date_closed) = Extract(QUARTER FROM DATE(NOW()))
        AND Extract(Year FROM date_closed) = Extract(Year FROM DATE(NOW()))
        or type='opportunity' and active = false and probability = 0 and user_id=%s
        AND Extract(QUARTER FROM date_deadline) = Extract(QUARTER FROM DATE(NOW()))
        AND Extract(Year FROM date_deadline) = Extract(Year FROM DATE(NOW()))
        GROUP BY active''' % (session_user_id, session_user_id))
        record_opportunity = dict(self._cr.fetchall())
        opportunity_ratio_value = 0.0
        if record_opportunity == {}:
            opportunity_ratio_value = 0.0
        else:
            total_opportunity_won = record_opportunity.get(False)
            total_opportunity_lost = record_opportunity.get(True)
            if total_opportunity_won is None:
                total_opportunity_won = 0
            if total_opportunity_lost is None:
                total_opportunity_lost = 0
                opportunity_ratio_value = 0.0
            if total_opportunity_lost > 0:
                opportunity_ratio_value = round(total_opportunity_won / total_opportunity_lost, 2)

        avg = 0
        if crm_lead_value == 1:
            self._cr.execute('''SELECT id, date_conversion, create_date
            FROM crm_lead WHERE date_conversion IS NOT NULL;''')
            data = self._cr.dictfetchall()
            for rec in data:
                date_close = rec['date_conversion']
                date_create = rec['create_date']
                avg = (date_close - date_create).seconds
        if crm_lead_value > 1:
            self._cr.execute('''SELECT id, date_conversion, create_date
            FROM crm_lead WHERE date_conversion IS NOT NULL;''')
            data1 = self._cr.dictfetchall()
            for rec in data1:
                date_close = rec['date_conversion']
                date_create = rec['create_date']
                avg = (date_close - date_create).seconds

        if crm_lead_value == 0:
            record_avg_time = 0
        else:
            record_avg_time = round(avg / crm_lead_value)

        data_quarter = {
            'customer': customer_value,
            'record': crm_lead_value,
            'record_op': opportunity_value,
            'record_rev_exp': exp_revenue_value,
            'record_rev': revenue_value,
            'record_ratio': ratio_value,
            'opportunity_ratio_value': str(opportunity_ratio_value),
            'avg_time': record_avg_time,
        }
        return data_quarter

    @api.model
    def crm_month(self, user_id):
        """Month CRM Dropdown Filter"""
        session_user_id = self.env.uid

        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != '0':
                self._cr.execute('''select COUNT(id) from res_partner where type != 'private' and active = true  
                                        and partner_share = true and user_id = %s ''' % user_id)
            else:
                self._cr.execute('''select COUNT(id) from res_partner where type != 'private' and active = true 
                                                and partner_share = true ''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != '0':
                self._cr.execute('''select COUNT(id) from res_partner where type != 'private' and active = true  and partner_share = true
                                                            and user_id = %s
                                                ''' % user_id)
            else:
                self._cr.execute('''select COUNT(id) from res_partner where type != 'private' and active = true  and partner_share = true
                                                            and (user_id = %s
                                                                 or (res_partner.user_id in 
                        	                                          (select crm_team_member.user_id from crm_team_member, crm_team 
                                                                           where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                                           and crm_team_member.active = true and crm_team.active = true))
                        	                                    )
                                                ''', (session_user_id, session_user_id))
        else:
            self._cr.execute('''select COUNT(id) from res_partner where type != 'private' and partner_share = true 
                                and active = true and user_id = %s  ''' % session_user_id)
        customer = self._cr.dictfetchall()
        customer_ids = [item['count'] for item in customer]
        customer_value = customer_ids[0]
        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != '0':
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.type='lead' 
                                           AND (crm_lead.user_id = %s or crm_lead.user_id is null)
                                           AND Extract(MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW()))
                                           AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))''' % user_id)
            else:
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.type='lead' AND
                                                Extract(MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW()))
                                                AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != '0':
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.type='lead' 
                                    AND (crm_lead.user_id = %s or crm_lead.user_id is null) 
                                    AND Extract(MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW()))
                                    AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                                    ''' % user_id)
            else:
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.type='lead' AND (
                                          (crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                            where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                            and crm_team_member.active = true and crm_team.active = true))
                			              OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
                			              OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team where crm_team.user_id = %s))
                			              ) 
                                AND Extract(MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW()))
                                AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                                ''', (session_user_id, session_user_id))
        else:
            self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.type='lead' 
                    AND (crm_lead.user_id = %s or crm_lead.user_id is null) 
                    AND Extract(MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW()))
                    AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                    ''' % session_user_id)
        record = self._cr.dictfetchall()
        rec_ids = [item['count'] for item in record]
        crm_lead_value = rec_ids[0]

        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != '0':
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.user_id = %s
                                    AND crm_lead.type = 'opportunity' AND Extract(MONTH FROM crm_lead.date_deadline
                                    ) = Extract(MONTH FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_deadline
                                    ) = Extract(Year FROM DATE(NOW( )))
                                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')''' % user_id)
            else:
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true
                                                AND crm_lead.type = 'opportunity' AND Extract(MONTH FROM crm_lead.date_deadline
                                                ) = Extract(MONTH FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_deadline
                                                ) = Extract(Year FROM DATE(NOW( )))
                                                and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != '0':
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.user_id = %s
                                                    AND crm_lead.type = 'opportunity' AND Extract(MONTH FROM crm_lead.date_deadline
                                                    ) = Extract(MONTH FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_deadline
                                                    ) = Extract(Year FROM DATE(NOW( )))
                                                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')''' % user_id)
            else:
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and (
                                                (crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                                    where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                    and crm_team_member.active = true and crm_team.active = true))
                			                    OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
                			                    OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team where crm_team.user_id = %s))
                			                    )
                                                AND crm_lead.type = 'opportunity' AND Extract(MONTH FROM crm_lead.date_deadline
                                                ) = Extract(MONTH FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_deadline
                                                ) = Extract(Year FROM DATE(NOW( )))
                                                and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')''',
                                 (session_user_id, session_user_id))
        else:
            self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.user_id = %s
                    AND crm_lead.type = 'opportunity' AND Extract(MONTH FROM crm_lead.date_deadline
                    ) = Extract(MONTH FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_deadline
                    ) = Extract(Year FROM DATE(NOW( )))
                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')''' % session_user_id)
        opportunity_data = self._cr.dictfetchall()
        opportunity_data_value = [item['count'] for item in opportunity_data]
        opportunity_value = opportunity_data_value[0]

        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != '0':
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                                    crm_lead.user_id = %s and type='opportunity' and active='true' AND Extract(
                                    MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW())) AND
                                    Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                    ''' % user_id)
            else:
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                                    type='opportunity' and active='true' AND Extract(
                                    MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW())) AND
                                    Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                    ''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != '0':
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                                    crm_lead.user_id = %s and type='opportunity' and active='true' AND Extract(
                                    MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW())) AND
                                    Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                    ''' % user_id)
            else:
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                                    ((crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                         where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                         and crm_team_member.active = true and crm_team.active = true))
                			          OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
                			          OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team where crm_team.user_id = %s)) )
                			        and type='opportunity' and active='true' AND Extract(
                                    MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW())) AND
                                    Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                    ''', (session_user_id, session_user_id))
        else:
            self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                    crm_lead.user_id = %s and type='opportunity' and active='true' AND Extract(
                    MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW())) AND
                    Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                    ''' % session_user_id)
        exp_revenue_data = self._cr.dictfetchall()
        exp_revenue_data_value = [item['sum'] for item in exp_revenue_data]
        exp_revenue_value = exp_revenue_data_value[0]
        if exp_revenue_value is None:
            exp_revenue_value = 0

        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != '0':
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                                    crm_lead.user_id = %s and type='opportunity' and active='true' 
                                    and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                    AND Extract(MONTH FROM crm_lead.date_closed) = Extract(MONTH FROM DATE(NOW()))
                                    AND Extract(Year FROM crm_lead.date_closed) = Extract(Year FROM DATE(NOW()))
                                 ''' % user_id)
            else:
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE type='opportunity' and active='true' 
                                                and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                                AND Extract(MONTH FROM crm_lead.date_closed) = Extract(MONTH FROM DATE(NOW()))
                                                AND Extract(Year FROM crm_lead.date_closed) = Extract(Year FROM DATE(NOW()))
                                                ''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != '0':
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                                                        crm_lead.user_id = %s and type='opportunity' and active='true' 
                                                and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                                AND Extract(MONTH FROM crm_lead.date_closed) = Extract(MONTH FROM DATE(NOW()))
                                                AND Extract(Year FROM crm_lead.date_closed) = Extract(Year FROM DATE(NOW()))
                                    ''' % user_id)
            else:
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                                                    ((crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                                           where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                           and crm_team_member.active = true and crm_team.active = true))
                    			                      OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
                    			                      OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team where crm_team.user_id = %s)) )
                                                    and type='opportunity' and active='true' 
                                                    and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                                    AND Extract(MONTH FROM crm_lead.date_closed) = Extract(MONTH FROM DATE(NOW()))
                                                    AND Extract(Year FROM crm_lead.date_closed) = Extract(Year FROM DATE(NOW()))
                                                    ''', (session_user_id, session_user_id))
        else:
            self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                    crm_lead.user_id = %s and type='opportunity' and active='true' 
                    and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                    AND Extract(MONTH FROM crm_lead.date_closed) = Extract(MONTH FROM DATE(NOW()))
                    AND Extract(Year FROM crm_lead.date_closed) = Extract(Year FROM DATE(NOW()))
                    ''' % session_user_id)

        revenue_data = self._cr.dictfetchall()
        revenue_data_value = [item['sum'] for item in revenue_data]
        revenue_value = revenue_data_value[0]
        if revenue_value is None:
            revenue_value = 0

        ratio_value = []
        if revenue_value == 0:
            ratio_value = 0
        if revenue_value > 0:
            if self.env.user.has_group('sales_team.group_sale_manager'):
                if user_id != '0':
                    self._cr.execute('''select case when b.count_two = 0 then 0 else (
                                                CAST(a.count_one as float) / CAST(b.count_two as float))end as final_count
                                                from (select COUNT(id) as count_one from crm_lead
                                                WHERE crm_lead.user_id = %s AND crm_lead.active = True  AND TYPE ='opportunity'
                                                AND crm_lead.probability = 100 AND Extract(MONTH FROM crm_lead.date_deadline
                                                ) = Extract(MONTH FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_open
                                                ) = Extract(Year FROM DATE(NOW())))a,
                                                (select COUNT(id) as count_two from crm_lead WHERE crm_lead.user_id = %s
                                                AND TYPE ='opportunity' AND Extract(
                                                MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW())) AND
                                                Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW())))b
                                                ''' % (user_id, user_id))
                else:
                    self._cr.execute('''select case when b.count_two = 0 then 0 else (
                                                                CAST(a.count_one as float) / CAST(b.count_two as float))end as final_count
                                                                from (select COUNT(id) as count_one from crm_lead
                                                                WHERE crm_lead.active = True  AND TYPE ='opportunity' AND crm_lead.probability = 100
                                                                AND Extract(MONTH FROM crm_lead.date_deadline
                                                                ) = Extract(MONTH FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_open
                                                                ) = Extract(Year FROM DATE(NOW())))a,
                                                                (select COUNT(id) as count_two from crm_lead WHERE TYPE ='opportunity'
                                                                AND Extract(MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW()))
                                                                AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW())))b
                                                                ''')
            elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
                if user_id != '0':
                    self._cr.execute('''select case when b.count_two = 0 then 0 else (
                                                CAST(a.count_one as float) / CAST(b.count_two as float))end as final_count
                                                from (select COUNT(id) as count_one from crm_lead
                                                WHERE crm_lead.user_id = %s AND crm_lead.active = True  AND TYPE ='opportunity'
                                                AND crm_lead.probability = 100 AND Extract(MONTH FROM crm_lead.date_deadline
                                                ) = Extract(MONTH FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_open
                                                ) = Extract(Year FROM DATE(NOW())))a,
                                                (select COUNT(id) as count_two from crm_lead WHERE crm_lead.user_id = %s
                                                AND TYPE ='opportunity' AND Extract(
                                                MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW())) AND
                                                Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW())))b
                                                ''' % (user_id, user_id))
                else:
                    self._cr.execute('''select case when b.count_two = 0 then 0 else (
                                                                CAST(a.count_one as float) / CAST(b.count_two as float))end as final_count
                                                                from (select COUNT(id) as count_one from crm_lead
                                                                WHERE ((crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                                                            where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                                            and crm_team_member.active = true and crm_team.active = true))
                    			                                        OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
                    			                                        OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team where crm_team.user_id = %s)) )
                                                                AND crm_lead.active = True  AND TYPE ='opportunity'
                                                                AND crm_lead.probability = 100 AND Extract(MONTH FROM crm_lead.date_deadline
                                                                ) = Extract(MONTH FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_open
                                                                ) = Extract(Year FROM DATE(NOW())))a,
                                                                (select COUNT(id) as count_two from crm_lead WHERE 
                                                                ((crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                                                        where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                                        and crm_team_member.active = true and crm_team.active = true))
                    			                                  OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
                    			                                  OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team where crm_team.user_id = %s)) )
                                                                AND TYPE ='opportunity' AND Extract(
                                                                MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW())) AND
                                                                Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW())))b
                                                                ''' % (
                    session_user_id, session_user_id, session_user_id, session_user_id))
            else:
                self._cr.execute('''select case when b.count_two = 0 then 0 else (
                            CAST(a.count_one as float) / CAST(b.count_two as float))end as final_count
                            from (select COUNT(id) as count_one from crm_lead
                            WHERE crm_lead.user_id = %s AND crm_lead.active = True  AND TYPE ='opportunity'
                            AND crm_lead.probability = 100 AND Extract(MONTH FROM crm_lead.date_deadline
                            ) = Extract(MONTH FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_open
                            ) = Extract(Year FROM DATE(NOW())))a,
                            (select COUNT(id) as count_two from crm_lead WHERE crm_lead.user_id = %s
                            AND TYPE ='opportunity' AND Extract(
                            MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW())) AND
                            Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW())))b
                            ''' % (session_user_id, session_user_id))
            ratio_value = [row[0] for row in self._cr.fetchall()]
            ratio_value = str(ratio_value)[1:-1]
            ratio_value = str(round(float(ratio_value) * 100, 2)) + "%"

        self._cr.execute('''SELECT active,count(active) FROM crm_lead
        where type='opportunity' and active = true and probability = 100 and user_id=%s
        AND Extract(MONTH FROM date_closed) = Extract(MONTH FROM DATE(NOW()))
        AND Extract(Year FROM date_closed) = Extract(Year FROM DATE(NOW()))
        or type='opportunity' and active = false and probability = 0 and user_id=%s
        AND Extract(MONTH FROM date_deadline) = Extract(MONTH FROM DATE(NOW()))
        AND Extract(Year FROM date_deadline) = Extract(Year FROM DATE(NOW()))
        GROUP BY active''' % (session_user_id, session_user_id))
        record_opportunity = dict(self._cr.fetchall())
        opportunity_ratio_value = 0.0
        if record_opportunity == {}:
            opportunity_ratio_value = 0.0
        else:
            total_opportunity_won = record_opportunity.get(False)
            total_opportunity_lost = record_opportunity.get(True)
            if total_opportunity_won is None:
                total_opportunity_won = 0
            if total_opportunity_lost is None:
                total_opportunity_lost = 0
                opportunity_ratio_value = 0.0
            if total_opportunity_lost > 0:
                opportunity_ratio_value = round(total_opportunity_won / total_opportunity_lost, 2)

        avg = 0
        if crm_lead_value == 1:
            self._cr.execute('''SELECT id, date_conversion, create_date
            FROM crm_lead WHERE date_conversion IS NOT NULL;''')
            data = self._cr.dictfetchall()
            for rec in data:
                date_close = rec['date_conversion']
                date_create = rec['create_date']
                avg = (date_close - date_create).seconds
        if crm_lead_value > 1:
            self._cr.execute('''SELECT id, date_conversion, create_date
            FROM crm_lead WHERE date_conversion IS NOT NULL;''')
            data1 = self._cr.dictfetchall()
            for rec in data1:
                date_close = rec['date_conversion']
                date_create = rec['create_date']
                avg = (date_close - date_create).seconds

        record_avg_time = 0 if crm_lead_value == 0 else round(avg / crm_lead_value)

        data_month = {
            'customer': customer_value,
            'record': crm_lead_value,
            'record_op': opportunity_value,
            'record_rev_exp': exp_revenue_value,
            'record_rev': revenue_value,
            'record_ratio': ratio_value,
            'opportunity_ratio_value': str(opportunity_ratio_value),
            'avg_time': record_avg_time,
        }
        return data_month

    @api.model
    def crm_week(self, user_id):
        """Week CRM Dropdown Filter"""
        session_user_id = self.env.uid

        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != '0':
                self._cr.execute('''select COUNT(id) from res_partner where type != 'private' and active = true  
                                        and partner_share = true and user_id = %s ''' % user_id)
            else:
                self._cr.execute('''select COUNT(id) from res_partner where type != 'private' and active = true 
                                                and partner_share = true ''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != '0':
                self._cr.execute('''select COUNT(id) from res_partner where type != 'private' and active = true  and partner_share = true
                                                            and user_id = %s
                                                ''' % user_id)
            else:
                self._cr.execute('''select COUNT(id) from res_partner where type != 'private' and active = true  and partner_share = true
                                                            and (user_id = %s
                                                                 or (res_partner.user_id in 
                        	                                          (select crm_team_member.user_id from crm_team_member, crm_team 
                                                                           where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                                           and crm_team_member.active = true and crm_team.active = true))
                        	                                    )
                                                ''', (session_user_id, session_user_id))
        else:
            self._cr.execute('''select COUNT(id) from res_partner where type != 'private' and partner_share = true 
                                and active = true and user_id = %s  ''' % session_user_id)
        customer = self._cr.dictfetchall()
        customer_ids = [item['count'] for item in customer]
        customer_value = customer_ids[0]
        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != '0':
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.type='lead' 
                                           AND (crm_lead.user_id = %s or crm_lead.user_id is null)
                                           AND Extract(MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW()))
                                           AND Extract(Week FROM crm_lead.date_deadline) = Extract(Week FROM DATE(NOW()))
                                           AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))''' % user_id)
            else:
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.type='lead' 
                                                AND Extract(MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW()))
                                                AND Extract(Week FROM crm_lead.date_deadline) = Extract(Week FROM DATE(NOW())) AND
                                                Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != '0':
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.type='lead' 
                                                           AND (crm_lead.user_id = %s or crm_lead.user_id is null)
                                                           AND Extract(MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW()))
                                                           AND Extract(Week FROM crm_lead.date_deadline) = Extract(Week FROM DATE(NOW()))
                                                           AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))''' % user_id)
            else:
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.type='lead' AND (
                                          (crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                            where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                            and crm_team_member.active = true and crm_team.active = true))
                			              OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
                			              OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team where crm_team.user_id = %s))
                			              )  
                                AND Extract(MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW()))
                                AND Extract(Week FROM crm_lead.date_deadline) = Extract(Week FROM DATE(NOW()))
                                AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                                ''', (session_user_id, session_user_id))
        else:
            self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.type='lead' 
                    AND (crm_lead.user_id = %s or crm_lead.user_id is null)
                    AND Extract(MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW()))
                    AND Extract(Week FROM crm_lead.date_deadline) = Extract(Week FROM DATE(NOW())) AND
                    Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                    ''' % session_user_id)

        record = self._cr.dictfetchall()
        rec_ids = [item['count'] for item in record]
        crm_lead_value = rec_ids[0]

        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != '0':
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.user_id = %s
                                    AND crm_lead.type = 'opportunity' AND Extract(MONTH FROM crm_lead.date_deadline
                                    ) = Extract(MONTH FROM DATE(NOW())) AND Extract(Week FROM crm_lead.date_deadline
                                    ) = Extract(Week FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_deadline
                                    ) = Extract(Year FROM DATE(NOW()))
                                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')''' % user_id)
            else:
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true 
                                                AND crm_lead.type = 'opportunity' AND Extract(MONTH FROM crm_lead.date_deadline
                                                ) = Extract(MONTH FROM DATE(NOW())) AND Extract(Week FROM crm_lead.date_deadline
                                                ) = Extract(Week FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_deadline
                                                ) = Extract(Year FROM DATE(NOW()))
                                                and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != '0':
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.user_id = %s
                                                    AND crm_lead.type = 'opportunity' AND Extract(MONTH FROM crm_lead.date_deadline
                                                    ) = Extract(MONTH FROM DATE(NOW())) AND Extract(Week FROM crm_lead.date_deadline
                                                    ) = Extract(Week FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_deadline
                                                    ) = Extract(Year FROM DATE(NOW()))
                                                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')''' % user_id)
            else:
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and (
                                                (crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                                    where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                    and crm_team_member.active = true and crm_team.active = true))
                			                    OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
                			                    OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team 
                			                    where crm_team.user_id = %s)))
                                                AND crm_lead.type = 'opportunity' AND Extract(MONTH FROM crm_lead.date_deadline
                                                ) = Extract(MONTH FROM DATE(NOW())) AND Extract(Week FROM crm_lead.date_deadline
                                                ) = Extract(Week FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_deadline
                                                ) = Extract(Year FROM DATE(NOW()))
                                                and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')''',
                                 (session_user_id, session_user_id))
        else:
            self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.user_id = %s
                    AND crm_lead.type = 'opportunity' AND Extract(MONTH FROM crm_lead.date_deadline
                    ) = Extract(MONTH FROM DATE(NOW())) AND Extract(Week FROM crm_lead.date_deadline
                    ) = Extract(Week FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_deadline
                    ) = Extract(Year FROM DATE(NOW()))
                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')''' % session_user_id)
        opportunity_data = self._cr.dictfetchall()
        opportunity_data_value = [item['count'] for item in opportunity_data]
        opportunity_value = opportunity_data_value[0]

        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != '0':
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                                    crm_lead.user_id = %s and type='opportunity' and active='true' AND Extract(
                                    MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW())) AND
                                    Extract(Week FROM crm_lead.date_deadline) = Extract(Week FROM DATE(NOW()))
                                    AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                    ''' % user_id)
            else:
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                                    type='opportunity' and active='true' AND Extract(
                                    MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW())) AND
                                    Extract(Week FROM crm_lead.date_deadline) = Extract(Week FROM DATE(NOW()))
                                    AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                    ''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != '0':
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                                    crm_lead.user_id = %s and type='opportunity' and active='true' AND Extract(
                                    MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW())) AND
                                    Extract(Week FROM crm_lead.date_deadline) = Extract(Week FROM DATE(NOW()))
                                    AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                    ''' % user_id)
            else:
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                                    ((crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                           where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                           and crm_team_member.active = true and crm_team.active = true))
                			          OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
                			          OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team 
                			             where crm_team.user_id = %s))) 
                			        and type='opportunity' and active='true' AND Extract(
                                    MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW())) AND
                                    Extract(Week FROM crm_lead.date_deadline) = Extract(Week FROM DATE(NOW()))
                                    AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                    ''', (session_user_id, session_user_id))
        else:
            self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                    crm_lead.user_id = %s and type='opportunity' and active='true' AND Extract(
                    MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW())) AND
                    Extract(Week FROM crm_lead.date_deadline) = Extract(Week FROM DATE(NOW()))
                    AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
                    and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                    ''' % session_user_id)
        exp_revenue_data = self._cr.dictfetchall()
        exp_revenue_data_value = [item['sum'] for item in exp_revenue_data]
        exp_revenue_value = exp_revenue_data_value[0]
        if exp_revenue_value is None:
            exp_revenue_value = 0

        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != '0':
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                                    crm_lead.user_id = %s and type='opportunity' and active='true' 
                                    and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                    AND Extract(MONTH FROM crm_lead.date_closed) = Extract(MONTH FROM DATE(NOW()))
                                    AND Extract(Week FROM crm_lead.date_closed) = Extract(Week FROM DATE(NOW()))
                                    AND Extract(Year FROM crm_lead.date_closed) = Extract(Year FROM DATE(NOW()))
                                    ''' % user_id)
            else:
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE type='opportunity' and active='true' 
                                            and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                            AND Extract(MONTH FROM crm_lead.date_closed) = Extract(MONTH FROM DATE(NOW()))
                                            AND Extract(Week FROM crm_lead.date_closed) = Extract(Week FROM DATE(NOW()))
                                            AND Extract(Year FROM crm_lead.date_closed) = Extract(Year FROM DATE(NOW()))
                                    ''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != '0':
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                                    crm_lead.user_id = %s and type='opportunity' and active='true' 
                                    and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                    AND Extract(MONTH FROM crm_lead.date_closed) = Extract(MONTH FROM DATE(NOW()))
                                    AND Extract(Week FROM crm_lead.date_closed) = Extract(Week FROM DATE(NOW()))
                                    AND Extract(Year FROM crm_lead.date_closed) = Extract(Year FROM DATE(NOW()))
                                    ''' % user_id)
            else:
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                                                ((crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                                    where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                    and crm_team_member.active = true and crm_team.active = true))
                			                      OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
                			                      OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team 
                			                        where crm_team.user_id = %s)))
                			                    and type='opportunity' and active='true' 
                                                and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                                AND Extract(MONTH FROM crm_lead.date_closed) = Extract(MONTH FROM DATE(NOW()))
                                                AND Extract(Week FROM crm_lead.date_closed) = Extract(Week FROM DATE(NOW()))
                                                AND Extract(Year FROM crm_lead.date_closed) = Extract(Year FROM DATE(NOW()))
                                                ''', (session_user_id, session_user_id))
        else:
            self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead WHERE
                    crm_lead.user_id = %s and type='opportunity' and active='true' 
                    and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                    AND Extract(MONTH FROM crm_lead.date_closed) = Extract(MONTH FROM DATE(NOW()))
                    AND Extract(Week FROM crm_lead.date_closed) = Extract(Week FROM DATE(NOW()))
                    AND Extract(Year FROM crm_lead.date_closed) = Extract(Year FROM DATE(NOW()))
                    ''' % session_user_id)

        revenue_data = self._cr.dictfetchall()
        revenue_data_value = [item['sum'] for item in revenue_data]
        revenue_value = revenue_data_value[0]
        if revenue_value is None:
            revenue_value = 0

        ratio_value = []
        if revenue_value == 0:
            ratio_value = 0
        if revenue_value > 0:
            if self.env.user.has_group('sales_team.group_sale_manager'):
                if user_id != '0':
                    self._cr.execute('''select case when b.count_two = 0 then 0 else (
                                                CAST(a.count_one as float) / CAST(b.count_two as float))end as final_count
                                                from (select COUNT(id) as count_one from crm_lead
                                                WHERE crm_lead.user_id = %s AND TYPE ='opportunity' AND crm_lead.active = True AND
                                                crm_lead.probability = 100 AND Extract(MONTH FROM crm_lead.date_deadline
                                                ) = Extract(MONTH FROM DATE(NOW())) AND Extract(Week FROM crm_lead.date_deadline
                                                ) = Extract(Week FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_open
                                                ) = Extract(Year FROM DATE(NOW())))a,
                                                (select COUNT(id) as count_two from crm_lead WHERE crm_lead.user_id = %s
                                                AND TYPE ='opportunity' AND Extract(MONTH
                                                FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW())) AND Extract(Week
                                                FROM crm_lead.date_deadline) = Extract(Week FROM DATE(NOW())) AND Extract(Year FROM
                                                crm_lead.date_deadline) = Extract(Year FROM DATE(NOW())))b
                                                ''' % (user_id, user_id))
                else:
                    self._cr.execute('''select case when b.count_two = 0 then 0 else (
                                                                CAST(a.count_one as float) / CAST(b.count_two as float))end as final_count
                                                                from (select COUNT(id) as count_one from crm_lead
                                                                WHERE TYPE ='opportunity' AND crm_lead.active = True AND
                                                                crm_lead.probability = 100 AND Extract(MONTH FROM crm_lead.date_deadline
                                                                ) = Extract(MONTH FROM DATE(NOW())) AND Extract(Week FROM crm_lead.date_deadline
                                                                ) = Extract(Week FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_open
                                                                ) = Extract(Year FROM DATE(NOW())))a,
                                                                (select COUNT(id) as count_two from crm_lead WHERE TYPE ='opportunity'
                                                                AND Extract(MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW())) 
                                                                AND Extract(Week FROM crm_lead.date_deadline) = Extract(Week FROM DATE(NOW())) 
                                                                AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW())))b
                                                                ''')
            elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
                if user_id != '0':
                    self._cr.execute('''select case when b.count_two = 0 then 0 else (
                                                CAST(a.count_one as float) / CAST(b.count_two as float))end as final_count
                                                from (select COUNT(id) as count_one from crm_lead
                                                WHERE crm_lead.user_id = %s AND TYPE ='opportunity' AND crm_lead.active = True AND
                                                crm_lead.probability = 100 AND Extract(MONTH FROM crm_lead.date_deadline
                                                ) = Extract(MONTH FROM DATE(NOW())) AND Extract(Week FROM crm_lead.date_deadline
                                                ) = Extract(Week FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_open
                                                ) = Extract(Year FROM DATE(NOW())))a,
                                                (select COUNT(id) as count_two from crm_lead WHERE crm_lead.user_id = %s
                                                AND TYPE ='opportunity' AND Extract(MONTH
                                                FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW())) AND Extract(Week
                                                FROM crm_lead.date_deadline) = Extract(Week FROM DATE(NOW())) AND Extract(Year FROM
                                                crm_lead.date_deadline) = Extract(Year FROM DATE(NOW())))b
                                                ''' % (user_id, user_id))
                else:
                    self._cr.execute('''select case when b.count_two = 0 then 0 else (
                                                                CAST(a.count_one as float) / CAST(b.count_two as float))end as final_count
                                                                from (select COUNT(id) as count_one from crm_lead
                                                                WHERE ((crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                                                            where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                                            and crm_team_member.active = true and crm_team.active = true))
                    			                                        OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
                    			                                        OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team 
                    			                                            where crm_team.user_id = %s)))
                                                                AND TYPE ='opportunity' AND crm_lead.active = True AND
                                                                crm_lead.probability = 100 AND Extract(MONTH FROM crm_lead.date_deadline
                                                                ) = Extract(MONTH FROM DATE(NOW())) AND Extract(Week FROM crm_lead.date_deadline
                                                                ) = Extract(Week FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_open
                                                                ) = Extract(Year FROM DATE(NOW())))a,
                                                                (select COUNT(id) as count_two from crm_lead WHERE 
                                                                ((crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                                                            where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                                            and crm_team_member.active = true and crm_team.active = true))
                    			                                  OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
                    			                                  OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team 
                    			                                            where crm_team.user_id = %s)))
                                                                AND TYPE ='opportunity' AND Extract(MONTH
                                                                FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW())) AND Extract(Week
                                                                FROM crm_lead.date_deadline) = Extract(Week FROM DATE(NOW())) AND Extract(Year FROM
                                                                crm_lead.date_deadline) = Extract(Year FROM DATE(NOW())))b
                                                                ''' % (
                    session_user_id, session_user_id, session_user_id, session_user_id))
            else:
                self._cr.execute('''select case when b.count_two = 0 then 0 else (
                            CAST(a.count_one as float) / CAST(b.count_two as float))end as final_count
                            from (select COUNT(id) as count_one from crm_lead
                            WHERE crm_lead.user_id = %s AND TYPE ='opportunity' AND crm_lead.active = True AND
                            crm_lead.probability = 100 AND Extract(MONTH FROM crm_lead.date_deadline
                            ) = Extract(MONTH FROM DATE(NOW())) AND Extract(Week FROM crm_lead.date_deadline
                            ) = Extract(Week FROM DATE(NOW())) AND Extract(Year FROM crm_lead.date_open
                            ) = Extract(Year FROM DATE(NOW())))a,
                            (select COUNT(id) as count_two from crm_lead WHERE crm_lead.user_id = %s
                            AND TYPE ='opportunity' AND Extract(MONTH
                            FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW())) AND Extract(Week
                            FROM crm_lead.date_deadline) = Extract(Week FROM DATE(NOW())) AND Extract(Year FROM
                            crm_lead.date_deadline) = Extract(Year FROM DATE(NOW())))b
                            ''' % (session_user_id, session_user_id))
            ratio_value = [row[0] for row in self._cr.fetchall()]
            ratio_value = str(ratio_value)[1:-1]
            ratio_value = str(round(float(ratio_value) * 100, 2)) + "%"

        self._cr.execute('''SELECT active,count(active) FROM crm_lead
        where type='opportunity' and active = true and probability = 100 and user_id=%s
        AND Extract(MONTH FROM crm_lead.date_closed) = Extract(MONTH FROM DATE(NOW()))
        AND Extract(Week FROM crm_lead.date_closed) = Extract(Week FROM DATE(NOW()))
        AND Extract(Year FROM crm_lead.date_closed) = Extract(Year FROM DATE(NOW()))
        or type='opportunity' and active = false and probability = 0 and user_id=%s
        AND Extract(MONTH FROM crm_lead.date_deadline) = Extract(MONTH FROM DATE(NOW()))
        AND Extract(Week FROM crm_lead.date_deadline) = Extract(Week FROM DATE(NOW()))
        AND Extract(Year FROM crm_lead.date_deadline) = Extract(Year FROM DATE(NOW()))
        GROUP BY active''' % (session_user_id, session_user_id))
        record_opportunity = dict(self._cr.fetchall())
        opportunity_ratio_value = 0.0
        if record_opportunity == {}:
            opportunity_ratio_value = 0.0
        else:
            total_opportunity_won = record_opportunity.get(False)
            total_opportunity_lost = record_opportunity.get(True)
            if total_opportunity_won is None:
                total_opportunity_won = 0
            if total_opportunity_lost is None:
                total_opportunity_lost = 0
                opportunity_ratio_value = 0.0
            if total_opportunity_lost > 0:
                opportunity_ratio_value = round(total_opportunity_won / total_opportunity_lost, 2)

        avg = 0
        if crm_lead_value == 1:
            self._cr.execute('''SELECT id, date_conversion, create_date
            FROM crm_lead WHERE date_conversion IS NOT NULL;''')
            data = self._cr.dictfetchall()
            for rec in data:
                date_close = rec['date_conversion']
                date_create = rec['create_date']
                avg = (date_close - date_create).seconds
        if crm_lead_value > 1:
            self._cr.execute('''SELECT id, date_conversion, create_date
            FROM crm_lead WHERE date_conversion IS NOT NULL;''')
            data1 = self._cr.dictfetchall()
            for rec in data1:
                date_close = rec['date_conversion']
                date_create = rec['create_date']
                avg = (date_close - date_create).seconds

        if crm_lead_value == 0:
            record_avg_time = 0
        else:
            record_avg_time = round(avg / crm_lead_value)

        data_week = {
            'customer': customer_value,
            'record': crm_lead_value,
            'record_op': opportunity_value,
            'record_rev_exp': exp_revenue_value,
            'record_rev': revenue_value,
            'record_ratio': ratio_value,
            'opportunity_ratio_value': str(opportunity_ratio_value),
            'avg_time': record_avg_time,
        }
        return data_week

    @api.model
    def crm_all(self, user_id):
        """All CRM Dropdown Filter"""
        session_user_id = self.env.uid

        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != '0':
                self._cr.execute('''select COUNT(id) from res_partner where type != 'private' and active = true  
                                        and partner_share = true and user_id = '%s' ''' % user_id)
            else:
                self._cr.execute('''select COUNT(id) from res_partner where type != 'private' and active = true 
                                                and partner_share = true ''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != '0':
                self._cr.execute('''select COUNT(id) from res_partner where type != 'private' and active = true  and partner_share = true
                                                            and user_id = '%s'
                                                ''' % user_id)
            else:
                self._cr.execute('''select COUNT(id) from res_partner where type != 'private' and active = true  and partner_share = true
                                                            and (user_id = '%s'
                                                                 or (res_partner.user_id in 
                        	                                          (select crm_team_member.user_id from crm_team_member, crm_team 
                                                                           where crm_team.user_id = '%s' and crm_team.id = crm_team_member.crm_team_id 
                                                                           and crm_team_member.active = true and crm_team.active = true))
                        	                                    )
                                                ''', (session_user_id, session_user_id))
        else:
            self._cr.execute('''select COUNT(id) from res_partner where type != 'private' and partner_share = true 
                                and active = true and user_id = '%s'  ''' % session_user_id)
        customer = self._cr.dictfetchall()
        customer_ids = [item['count'] for item in customer]
        customer_value = customer_ids[0]

        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != '0':
                self._cr.execute('''select COUNT(id) from crm_lead where crm_lead.active = true and crm_lead.type='lead' 
                                and (crm_lead.user_id = '%s' or crm_lead.user_id is null) ''' % user_id)
            else:
                self._cr.execute(
                    '''select COUNT(id) from crm_lead where crm_lead.active = true and crm_lead.type='lead' ''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != '0':
                self._cr.execute('''select COUNT(id) from crm_lead where crm_lead.active = true and crm_lead.type='lead' 
                                                and (crm_lead.user_id = '%s' or crm_lead.user_id is null) ''' % user_id)
            else:
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.type='lead' and (
                                          (crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                            where crm_team.user_id = '%s' and crm_team.id = crm_team_member.crm_team_id 
                                            and crm_team_member.active = true and crm_team.active = true))
                			              OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
                			              OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team where crm_team.user_id = '%s'))
                			              )
                                ''', (session_user_id, session_user_id))
        else:
            self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.type='lead' 
            and (crm_lead.user_id = '%s' or crm_lead.user_id is null) ''' % session_user_id)
        record = self._cr.dictfetchall()
        rec_ids = [item['count'] for item in record]
        crm_lead_value = rec_ids[0]

        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != '0':
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.user_id = %s
                                        AND crm_lead.type = 'opportunity' 
                                        and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                        ''' % user_id)
            else:
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.type = 'opportunity' 
                            and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31') ''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != '0':
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.user_id = %s
                                           AND crm_lead.type = 'opportunity' 
                                           and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                 ''' % user_id)
            else:
                self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.type='opportunity' and (
                                           (crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                             where crm_team.user_id = '%s' and crm_team.id = crm_team_member.crm_team_id 
                                             and crm_team_member.active = true and crm_team.active = true))
                            			    OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
                            			    OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team where crm_team.user_id = '%s'))
                            			    )
                            		and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                            	''', (session_user_id, session_user_id))
        else:
            self._cr.execute('''select COUNT(id) from crm_lead WHERE crm_lead.active = true and crm_lead.user_id = %s
                        AND crm_lead.type = 'opportunity' 
                        and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                        ''' % session_user_id)
        opportunity_data = self._cr.dictfetchall()
        opportunity_data_value = [item['count'] for item in opportunity_data]
        opportunity_value = opportunity_data_value[0]

        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != '0':
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead
                                        WHERE crm_lead.user_id = %s and type='opportunity' and active='true' 
                                        and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                        ''' % user_id)
            else:
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead
                                        WHERE type='opportunity' and active='true' 
                                        and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                        ''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != '0':
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead
                                        WHERE crm_lead.user_id = %s and type='opportunity' and active='true' 
                                        and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                        ''' % user_id)
            else:
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead
                                        WHERE ((crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                                    where crm_team.user_id = '%s' and crm_team.id = crm_team_member.crm_team_id 
                                                    and crm_team_member.active = true and crm_team.active = true))
                            			        OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
                            			        OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team where crm_team.user_id = '%s'))
                            			       ) and type='opportunity' and active='true' 
                            			       and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                        ''', (session_user_id, session_user_id))
        else:
            self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead
                        WHERE crm_lead.user_id = %s and type='opportunity' and active='true' 
                        and x_lead_status in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                        ''' % session_user_id)
        exp_revenue_data = self._cr.dictfetchall()
        exp_revenue_data_value = [item['sum'] for item in exp_revenue_data]
        exp_revenue_value = exp_revenue_data_value[0]
        if exp_revenue_value is None:
            exp_revenue_value = 0

        if self.env.user.has_group('sales_team.group_sale_manager'):
            if user_id != '0':
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead
                                        WHERE crm_lead.user_id = %s and type='opportunity' and active='true' 
                                        and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                        ''' % user_id)
            else:
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead
                                                    WHERE type='opportunity' and active='true' 
                                                    and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                                    ''')
        elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            if user_id != '0':
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead
                                        WHERE crm_lead.user_id = %s and type='opportunity' and active='true' 
                                        and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                        ''' % user_id)
            else:
                self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead
                                                    WHERE ((crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                                              where crm_team.user_id = '%s' and crm_team.id = crm_team_member.crm_team_id 
                                                              and crm_team_member.active = true and crm_team.active = true))
                            			                    OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
                            			                    OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team where crm_team.user_id = '%s'))
                            			                  ) 
                            			            and type='opportunity' and active='true' 
                                                    and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                                                    ''', (session_user_id, session_user_id))
        else:
            self._cr.execute('''select SUM(crm_lead.expected_revenue) from crm_lead
                        WHERE crm_lead.user_id = %s and type='opportunity' and active='true' 
                        and x_lead_status not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '30', '31')
                        ''' % session_user_id)
        revenue_data = self._cr.dictfetchall()
        revenue_data_value = [item['sum'] for item in revenue_data]
        revenue_value = revenue_data_value[0]
        if revenue_value is None:
            revenue_value = 0

        ratio_value = []
        if revenue_value == 0:
            ratio_value = 0
        if revenue_value > 0:
            if self.env.user.has_group('sales_team.group_sale_manager'):
                if user_id != '0':
                    self._cr.execute('''select case when b.count_two = 0 then 0 else (
                                                    CAST(a.count_one as float) / CAST(b.count_two as float))end as final_count from (
                                                    select COUNT(id) as count_one from crm_lead WHERE crm_lead.user_id = %s 
                                                    AND TYPE ='opportunity' AND crm_lead.active = True AND crm_lead.probability = 100 )a,
                                                    (select COUNT(id) as count_two from crm_lead WHERE crm_lead.user_id = %s 
                                                    AND TYPE ='opportunity' )b
                                                    ''' % (user_id, user_id))
                else:
                    self._cr.execute('''select case when b.count_two = 0 then 0 else (
                                                    CAST(a.count_one as float) / CAST(b.count_two as float))end as final_count from (
                                                    select COUNT(id) as count_one from crm_lead WHERE 
                                                    TYPE ='opportunity' AND crm_lead.active = True AND crm_lead.probability = 100 )a,
                                                    (select COUNT(id) as count_two from crm_lead WHERE TYPE ='opportunity' )b
                                                    ''')
            elif self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
                if user_id != '0':
                    self._cr.execute('''select case when b.count_two = 0 then 0 else (
                                                    CAST(a.count_one as float) / CAST(b.count_two as float))end as final_count from (
                                                    select COUNT(id) as count_one from crm_lead WHERE crm_lead.user_id = %s 
                                                    AND TYPE ='opportunity' AND crm_lead.active = True AND crm_lead.probability = 100 )a,
                                                    (select COUNT(id) as count_two from crm_lead WHERE crm_lead.user_id = %s 
                                                    AND TYPE ='opportunity' )b
                                                    ''' % (user_id, user_id))
                else:
                    self._cr.execute('''select case when b.count_two = 0 then 0 else (
                                                    CAST(a.count_one as float) / CAST(b.count_two as float))end as final_count from (
                                                    select COUNT(id) as count_one from crm_lead WHERE ((crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                                                  where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                                  and crm_team_member.active = true and crm_team.active = true))
                                			                    OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
                                			                    OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team where crm_team.user_id = %s))
                                			                  ) 
                                                    AND TYPE ='opportunity' AND crm_lead.active = True AND crm_lead.probability = 100 )a,
                                                    (select COUNT(id) as count_two from crm_lead WHERE ((crm_lead.user_id in (select crm_team_member.user_id from crm_team_member, crm_team 
                                                                  where crm_team.user_id = %s and crm_team.id = crm_team_member.crm_team_id 
                                                                  and crm_team_member.active = true and crm_team.active = true))
                                			                    OR (crm_lead.user_id is NULL AND crm_lead.team_id is NULL)
                                			                    OR (crm_lead.user_id is NULL AND crm_lead.team_id IN (select id from crm_team where crm_team.user_id = %s))
                                			                  ) 
                                                    AND TYPE ='opportunity' )b
                                                    ''' % (
                    session_user_id, session_user_id, session_user_id, session_user_id))
            else:
                self._cr.execute('''select case when b.count_two = 0 then 0 else (
                                CAST(a.count_one as float) / CAST(b.count_two as float))end as final_count from (
                                select COUNT(id) as count_one from crm_lead WHERE crm_lead.user_id = %s 
                                AND TYPE ='opportunity' AND crm_lead.active = True AND crm_lead.probability = 100 )a,
                                (select COUNT(id) as count_two from crm_lead WHERE crm_lead.user_id = %s 
                                AND TYPE ='opportunity' )b
                                ''' % (session_user_id, session_user_id))
            ratio_value = [row[0] for row in self._cr.fetchall()]
            ratio_value = str(ratio_value)[1:-1]
            ratio_value = str(round(float(ratio_value) * 100, 2)) + "%"

        self._cr.execute('''SELECT active,count(active) FROM crm_lead
            where type='opportunity' and active = true and probability = 100 and user_id=%s
            or type='opportunity' and active = false and probability = 0 and user_id=%s
            GROUP BY active''' % (session_user_id, session_user_id))
        record_opportunity = dict(self._cr.fetchall())
        opportunity_ratio_value = 0.0
        if record_opportunity == {}:
            opportunity_ratio_value = 0.0
        else:
            total_opportunity_won = record_opportunity.get(False)
            total_opportunity_lost = record_opportunity.get(True)
            if total_opportunity_won is None:
                total_opportunity_won = 0
            if total_opportunity_lost is None:
                total_opportunity_lost = 0
                opportunity_ratio_value = 0.0
            if total_opportunity_lost > 0:
                opportunity_ratio_value = round(total_opportunity_won / total_opportunity_lost, 2)

        avg = 0
        if crm_lead_value == 1:
            self._cr.execute('''SELECT id, date_conversion, create_date
                FROM crm_lead WHERE date_conversion IS NOT NULL;''')
            data = self._cr.dictfetchall()
            for rec in data:
                date_close = rec['date_conversion']
                date_create = rec['create_date']
                avg = (date_close - date_create).seconds
        if crm_lead_value > 1:
            self._cr.execute('''SELECT id, date_conversion, create_date
                FROM crm_lead WHERE date_conversion IS NOT NULL;''')
            data1 = self._cr.dictfetchall()
            for rec in data1:
                date_close = rec['date_conversion']
                date_create = rec['create_date']
                avg = (date_close - date_create).seconds

        if crm_lead_value == 0:
            record_avg_time = 0
        else:
            record_avg_time = round(avg / crm_lead_value)

        data_all = {
            'customer': customer_value,
            'record': crm_lead_value,
            'record_op': opportunity_value,
            'record_rev_exp': exp_revenue_value,
            'record_rev': revenue_value,
            'record_ratio': ratio_value,
            'opportunity_ratio_value': str(opportunity_ratio_value),
            'avg_time': record_avg_time,
        }
        return data_all


class CampaignSmartButton(models.Model):
    _inherit = 'utm.campaign'

    total_ratio = fields.Float(compute='_compute_ratio')

    def get_ratio(self):
        """Onclick of Smart Button"""
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Win Loss Ratio',
            'view_mode': 'kanban',
            'res_model': 'crm.lead',
            'domain': [['user_id', '=', self.env.uid], "|",
                       "&", ["active", "=", True], ["probability", '=', 100],
                       "&", ["active", "=", False], ["probability", '=', 0]
                       ],
            'context': "{'create': False,'records_draggable': False}"
        }

    def _compute_ratio(self):
        """Compute the Win Loss Ratio"""
        total_won = self.env['crm.lead'].search_count(
            [('active', '=', True), ('probability', '=', 100),
             ('user_id', '=', self.env.uid)])
        total_lose = self.env['crm.lead'].search_count(
            [('active', '=', False), ('probability', '=', 0),
             ('user_id', '=', self.env.uid)])

        if total_lose == 0:
            ratio = 0
        else:
            ratio = round(total_won / total_lose, 2)
        self.total_ratio = ratio
