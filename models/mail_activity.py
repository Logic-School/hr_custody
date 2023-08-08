from odoo import fields, api, models

class MailActivityInherit(models.Model):
    _inherit = "mail.activity"
    custody_request = fields.Many2one('hr.custody',string="Payment Request")