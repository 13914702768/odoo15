# -*- coding: UTF-8 -*-
from odoo import api, fields, models

class Lead2OpportunityPartnerXks(models.TransientModel):
    _inherit = "crm.lead2opportunity.partner"


    def action_apply_xks(self):
        if self.name == 'merge':
            result_opportunity = self._action_merge_xks()
        else:
            result_opportunity = self._action_convert_xks()

        return result_opportunity.redirect_lead_opportunity_view()

    def _action_merge_xks(self):
        to_merge = self.duplicated_lead_ids
        result_opportunity = to_merge.merge_opportunity(auto_unlink=False)
        result_opportunity.action_unarchive()

        if result_opportunity.type == "lead":
            self._convert_and_allocate_xks(result_opportunity, [self.user_id.id], team_id=self.team_id.id)
        else:
            if not result_opportunity.user_id or self.force_assignment:
                result_opportunity.write({
                    'user_id': self.user_id.id,
                    'team_id': self.team_id.id,
                })
        (to_merge - result_opportunity).unlink()
        return result_opportunity

    def _action_convert_xks(self):
        """ """
        result_opportunities = self.env['crm.lead'].browse(self._context.get('active_ids', []))
        self._convert_and_allocate_xks(result_opportunities, [self.user_id.id], team_id=self.team_id.id)
        return result_opportunities[0]

    def _convert_and_allocate_xks(self, leads, user_ids, team_id=False):
        self.ensure_one()

        for lead in leads:
            if lead.active and self.action != 'nothing':
                self._convert_handle_partner_xks(
                    lead, self.action, self.partner_id.id or lead.partner_id.id)

            lead.convert_opportunity_xks(lead.partner_id.id, user_ids=False, team_id=False)

        leads_to_allocate = leads
        if not self.force_assignment:
            leads_to_allocate = leads_to_allocate.filtered(lambda lead: not lead.user_id)

        if user_ids:
            leads_to_allocate._handle_salesmen_assignment(user_ids, team_id=team_id)

    def _convert_handle_partner_xks(self, lead, action, partner_id):
        # used to propagate user_id (salesman) on created partners during conversion
        lead.with_context(default_user_id=self.user_id.id)._handle_partner_assignment(
            force_partner_id=partner_id,
            create_missing=(action == 'create')
        )

