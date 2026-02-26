from odoo import fields, models, Command
from odoo.exceptions import UserError

class UserCompensation(models.Model):
    _name = 'user.compensation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    amount = fields.Monetary(currency_field='currency_id', readonly=False)
    state = fields.Selection([
        ('waiting', 'Waiting'),
        ('done', 'Done'),
        ('canceled', 'Canceled')
    ], default='waiting', tracking=True)
    dashboard_id = fields.Many2one('benefits.dashboard', ondelete='cascade')
    type_compensation = fields.Many2one('category.compensation', string='Compensation Type', required=True)

    account_move_id = fields.Many2one('account.move', string='Vendor Bill', readonly=True)

    date_create = fields.Date(string='Date', default=fields.Date.context_today, readonly=True)

    # Поле для отображения прикрепленных файлов
    attachment_ids = fields.Many2many(
        'ir.attachment',
        relation='user_compensation_attachment_rel',
        column1='compensation_id',
        column2='attachment_id',
        compute='_compute_attachment_ids',
        string="Attachments"
    )

    def _compute_attachment_ids(self):
        for record in self:
            record.attachment_ids = self.env['ir.attachment'].search([
                ('res_model', '=', self._name),
                ('res_id', '=', record.id)
            ])
    def send_email_employee(self):
        for record in self:
            if record.state == 'done':
                res_state = 'approved'
            if record.state == 'canceled':
                res_state = 'canceled'

            record.message_post(
                body=f"Hi! Your compensation was <strong>{res_state}</strong>({record.type_compensation.name}).",
                message_type='email',
                body_is_html=True,
                subtype_xmlid="mail.mt_comment",
                partner_ids=[record.employee_id.user_id.partner_id.id])

    def approve_compensation(self):
        for record in self:
            record.write({'state': 'done'})

    def canceled_compensation(self):
        for record in self:
            record.write({'state': 'canceled'})

    def action_canceled(self):
        # self.dashboard_id.write({'total':self.dashboard_id.total+self.amount})
        self.write({'state': 'canceled'})

    def action_done(self):
        self.write({'state': 'done'})

    def write(self, vals):
        if 'state' not in vals:
            return super().write(vals)

        for record in self:
            old_state = record.state
            new_state = vals['state']

            # если статус не меняется
            if old_state == new_state:
                continue

            # переход waiting → canceled
            if old_state in ('waiting', 'done') and new_state == 'canceled':
                record.dashboard_id.total += record.amount

                # переход canceled → waiting (если разрешишь)
            if old_state == 'canceled' and new_state == 'done':
                record.dashboard_id.total -= record.amount

        return super().write(vals)

    def create_account_move_user(self):
        self.ensure_one()
        if self.account_move_id:
            raise UserError("Bill already created")

        partner = self.employee_id.work_contact_id

        # Берём журнал покупок
        journal = self.env['account.journal'].search(
            [('type', '=', 'purchase')],
            limit=1
        )

        if not journal:
            raise UserError("No Purchase Journal found")

        # Счёт расходов (можно сделать настраиваемым)
        expense_account = self.env['account.account'].search(
            [('account_type', '=', 'expense')],
            limit=1
        )

        if not expense_account:
            raise UserError("No expense account found")

        move = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': partner.id,
            'journal_id': journal.id,
            'invoice_date': fields.Date.today(),
            'invoice_origin': self.employee_id.name,
            'invoice_line_ids': [
                Command.create({
                    'name': f'Employee Benefit - {self.employee_id.name}({self.type_compensation.name})',
                    'quantity': 1,
                    'price_unit': self.amount,
                    'account_id': expense_account.id,
                })
            ],
        })
        move.action_post()
        self.account_move_id = move.id

        self.message_post(
            body=f"Vendor Bill <b>{move.name}</b> has been created.",
            body_is_html = True
        )


    def action_open_vendor_bill(self):
        self.ensure_one()

        if not self.account_move_id:
            raise UserError("No Vendor Bill created yet")

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.account_move_id.id,
            'view_mode': 'form',
        }