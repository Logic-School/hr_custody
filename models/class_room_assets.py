from odoo import fields, models, api, _


class ClassRoomAssets(models.Model):
    _name = 'class.room.assets'
    _description = 'Class Room Assets'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name')
