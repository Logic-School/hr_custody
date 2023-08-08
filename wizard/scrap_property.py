from odoo import models,fields,api
from datetime import datetime

class ScrapProperty(models.TransientModel):
    _name = "property.scrap.wizard"
    property_id = fields.Many2one('custody.property',default= lambda self: self._context.get('property_id'))
    is_scrap = fields.Boolean(string="Is Scrap")
    scrap_money = fields.Monetary(string="Scrap Credit")
    scrap_reason = fields.Text(string="Reason")
    scrap_date = fields.Date(string="Scrap Date", default=datetime.today())
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
    
    def convert_to_scrap(self):
        self.property_id.write({
            'is_scrap': True,
            'scrap_money': self.scrap_money,
            'scrap_reason': self.scrap_reason,
            'scrap_date': self.scrap_date,
        })