from odoo import fields, models

class CategoryCompensation(models.Model):
    _name = "category.compensation"
    _description = "Category Compensation"
    _rec_name = "name"

    name = fields.Char(string="Name", required=True)
