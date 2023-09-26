from odoo import models,fields,api
from datetime import datetime

class RepairWizard(models.TransientModel):
    _name = "property.repair.wizard"
    property_id = fields.Many2one('custody.property',default = lambda self: self._context.get('property_id'))
    description = fields.Text(string="Description",required=True)
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
    date = fields.Date(string="Date", default = datetime.today())
    def action_create(self):
        self.env['custody.property.repair'].create({
            'property_id': self.property_id.id,
            'description': self.description,
            'repair_cost': self.repair_cost,
            'date': self.date
        })