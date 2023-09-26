from odoo import models,api,fields

class PropertyRepair(models.Model):
    _name="custody.property.repair"

    property_id = fields.Many2one('custody.property')
    description = fields.Text(string="Description")
    company_id = fields.Many2one(
            'res.company', store=True, copy=False,
            string="Company",
            default=lambda self: self.env.user.company_id.id,
            readonly=True)
    currency_id = fields.Many2one(
            'res.currency', string="Currency",
            related='company_id.currency_id',
            default=lambda
            self: self.env.user.company_id.currency_id.id,
            readonly=True)
    repair_cost = fields.Monetary(string="Repair Cost")
    date = fields.Date(string="Date")


