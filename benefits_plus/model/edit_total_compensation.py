from odoo import fields, models
from odoo.exceptions import UserError

class EditTotalCompensation(models.TransientModel):
    _name = 'edit.total.compensation'
    _description = 'Edit Total Compensation'

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    edit_total = fields.Monetary(currency_field='currency_id', readonly=False, default=1000)

    selected_count = fields.Integer(default=lambda self: len(self.env.context.get('active_ids', [])),readonly=True)

    def submit_edit_total_employee(self):
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')

        if not active_ids:
            raise UserError("No records selected.")

        dashboards = self.env[active_model].browse(active_ids)

        dashboards.write({'add_benefits': self.edit_total})