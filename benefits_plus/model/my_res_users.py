from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    has_group_benefits = fields.Boolean(
        string="Benefits Access",
        compute="_compute_has_group_benefits",
        inverse="_inverse_has_group_benefits"
    )

    def _compute_has_group_benefits(self):
        group = self.env.ref('benefits_plus.group_benefits_manage')
        if not group:
            return
        for user in self:
            user.has_group_benefits = group in user.groups_id

    def _inverse_has_group_benefits(self):
        group = self.env.ref('benefits_plus.group_benefits_manage')
        if not group:
            return
        for user in self:
            if user.has_group_benefits:
                user.groups_id = [(4, group.id)]
            else:
                user.groups_id = [(3, group.id)]