from odoo import fields, models, api
from odoo.exceptions import ValidationError

class BenefitsDashboard(models.Model):
    _name = 'benefits.dashboard'
    _description = 'Benefits Dashboard'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string='Employee', default=lambda self: self.env.user.employee_id, readonly=True, required=True)

    currency_id = fields.Many2one('res.currency',default=lambda self: self.env.company.currency_id)
    total = fields.Monetary(currency_field='currency_id', readonly=True, default=1000.0)

    add_benefits = fields.Monetary(currency_field='currency_id', string='Monthly additions', default=1000.0)

    history_ids = fields.One2many('user.compensation', 'dashboard_id', domain=[('state', '!=', 'waiting')])
    waiting_ids = fields.One2many('user.compensation', 'dashboard_id', domain=[('state', '=', 'waiting')])

    _sql_constraints = [
        ('employee_unique', 'unique(employee_id)', 'Dashboard already exists for this employee!')
    ]

    @api.model
    def open_dashboard(self):
        employee = self.env.user.employee_id

        if not employee:
            raise ValidationError("Current user has no related employee record.")

        dashboard = self.search([
            ('employee_id', '=', employee.id)
        ], limit=1)

        if not dashboard:
            dashboard = self.create({
                'employee_id': employee.id,
                'currency_id': self.env.company.currency_id.id,
                'total': 0.0,
            })
        print(dashboard, ' - ', dashboard.id)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Benefits Dashboard',
            'res_model': 'benefits.dashboard',
            'view_mode': 'form',
            'res_id': dashboard.id,
            'target': 'current',
        }

    def button_submit_compensation(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Submit compensation',
            'res_model': 'create.user.compensation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'custom_user_data_id': self.id}
        }

    def button_edit_total_employee(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Edit total',
            'res_model': 'edit.total.compensation',
            'view_mode': 'form',
            'target': 'new',
            'context':  {
                'active_ids': self.ids,
                'active_model': self._name,
            }
        }

    @api.model
    def _add_benefits_employee(self):
        dashboards = self.search([])
        for dashboard in dashboards:
            dashboard.total += dashboard.add_benefits
