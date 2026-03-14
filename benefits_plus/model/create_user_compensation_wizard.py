from odoo import fields, models
from odoo.exceptions import ValidationError

class CreateUserCompensation(models.TransientModel):
    _name = 'create.user.compensation.wizard'

    total_compensation = fields.Monetary(currency_field='currency_id', string='Summa Compensation', readonly=False)
    employee_id = fields.Many2one('hr.employee', string='Employee', default=lambda self: self.env.user.employee_id, readonly=True, required=True)
    type_compensation = fields.Many2one('category.compensation', string='Type compensation', readonly=False, required=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    attachment_ids = fields.Many2many('ir.attachment', string="Attachments", required=True)

    # benefits_total = fields.Monetary(string='Benefits Total', related='dashboard_id.total', currency_field='currency_id', readonly=True)

    def add_compensation_user(self):
        self.ensure_one()
        if not self.id:
            self.flush()
        dashboard = self.env['benefits.dashboard'].browse(self.env.context.get('custom_user_data_id'))
        print(self.total_compensation, ' - ', self.employee_id.name, ' - ', self.type_compensation.name)

        if not dashboard:
            raise ValidationError('Dashboard not found')

        if self.total_compensation > dashboard.total:
            raise ValidationError(f"Amount exceeds available total. Your benefits-compensation is {dashboard.total}.")

        compensation = self.env['user.compensation'].create({
            'employee_id': self.employee_id.id,
            'amount': self.total_compensation,
            'currency_id': self.currency_id.id,
            'type_compensation': self.type_compensation.id,
            'state': 'waiting',
            'dashboard_id': dashboard.id,
            'date_create': fields.Date.context_today(self),
        })
        # проверка, чтобы не возникло ошибок, если файлов нет
        if self.attachment_ids:
            self.attachment_ids.write({
                'res_model': 'user.compensation',
                'res_id': compensation.id,
            })

        dashboard.write({'total': dashboard.total - self.total_compensation})

        return {'type': 'ir.actions.act_window_close'}


