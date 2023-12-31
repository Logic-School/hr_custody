# -*- coding: utf-8 -*-

from datetime import date, datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError


class HrCustody(models.Model):
    """
        Hr custody contract creation model.
        """
    _name = 'hr.custody'
    _description = 'Hr Custody Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    read_only = fields.Boolean(string="check field")

    @api.onchange('employee')
    def _compute_read_only(self):
        """ Use this function to check weather the user has the permission to change the employee"""
        res_user = self.env['res.users'].search([('id', '=', self._uid)])
        print(res_user.has_group('hr.group_hr_user'))
        if res_user.has_group('hr.group_hr_user') or res_user.has_group('hr_custody.group_custody_property_admin'):
            self.read_only = True
        else:
            self.read_only = False

    def mail_reminder(self):
        now = datetime.now() + timedelta(days=1)
        date_now = now.date()
        match = self.search([('state', '=', 'approved')])
        for i in match:
            if i.return_date:
                exp_date = fields.Date.from_string(i.return_date)
                if exp_date <= date_now:
                    base_url = self.env['ir.config_parameter'].get_param('web.base.url')
                    url = base_url + _('/web#id=%s&view_type=form&model=hr.custody&menu_id=') % i.id
                    mail_content = _('Hi %s,<br>As per the %s you took %s on %s for the reason of %s. S0 here we '
                                     'remind you that you have to return that on or before %s. Otherwise, you can '
                                     'renew the reference number(%s) by extending the return date through following '
                                     'link.<br> <div style = "text-align: center; margin-top: 16px;"><a href = "%s"'
                                     'style = "padding: 5px 10px; font-size: 12px; line-height: 18px; color: #FFFFFF; '
                                     'border-color:#875A7B;text-decoration: none; display: inline-block; '
                                     'margin-bottom: 0px; font-weight: 400;text-align: center; vertical-align: middle; '
                                     'cursor: pointer; white-space: nowrap; background-image: none; '
                                     'background-color: #875A7B; border: 1px solid #875A7B; border-radius:3px;">'
                                     'Renew %s</a></div>') % \
                                   (i.employee.name, i.name, i.custody_name.name, i.date_request, i.purpose,
                                    date_now, i.name, url, i.name)
                    main_content = {
                        'subject': _('REMINDER On %s') % i.name,
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': i.employee.work_email,
                    }
                    mail_id = self.env['mail.mail'].create(main_content)
                    mail_id.mail_message_id.body = mail_content
                    mail_id.send()
                    if i.employee.user_id:
                        mail_id.mail_message_id.write(
                            {'needaction_partner_ids': [(4, i.employee.user_id.partner_id.id)]})
                        mail_id.mail_message_id.write({'partner_ids': [(4, i.employee.user_id.partner_id.id)]})

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('hr.custody')
        return super(HrCustody, self).create(vals)

    def sent(self):
        # if not self.return_date
        self.state = 'to_approve'
        self.activity_schedule(
            'hr_custody.mail_activity_type_custody_request',
            custody_request = self.id,
            user_id = self.hr_manager.id,
            # date_deadline=self.payment_expect_date,
            # is_pay_approve_request=True,
            summary=f"Custody Request of {self.custody_name.name} from {self.env.user.name}"
        )

    def send_mail(self):
        template = self.env.ref('hr_custody.custody_email_notification_template')
        self.env['mail.template'].browse(template.id).send_mail(self.id)
        self.mail_send = True

    def set_to_draft(self):
        self.state = 'draft'

    def renew_approve(self):
        for custody in self.env['hr.custody'].search([('custody_name', '=', self.custody_name.id)]):
            if custody.state == "approved":
                raise UserError(_("Custody is not available now"))
        self.return_date = self.renew_date
        self.renew_date = ''
        self.state = 'approved'

    def renew_refuse(self):
        for custody in self.env['hr.custody'].search([('custody_name', '=', self.custody_name.id)]):
            if custody.state == "approved":
                raise UserError(_("Custody is not available now"))
        self.renew_date = ''
        self.state = 'approved'

    def approve(self):
        for custody in self.env['hr.custody'].search([('custody_name', '=', self.custody_name.id)]):
            if custody.state == "approved":
                raise UserError(_("Custody is not available now"))
        self.env['mail.activity'].search([('custody_request','=',self.id)],limit=1).unlink()
        self.state = 'approved'

    def set_to_return(self):
        self.state = 'returned'
        self.return_date = date.today()

    # # return date validation
    # @api.constrains('return_date')
    # def validate_return_date(self):
    #     if self.return_date < self.date_request:
    #         raise Warning('Please Give Valid Return Date')

    name = fields.Char(string='Code', copy=False, help="Code")
    company_id = fields.Many2one('res.company', 'Company', readonly=True, help="Company",
                                 default=lambda self: self.env.user.company_id)
    rejected_reason = fields.Text(string='Rejected Reason', copy=False, readonly=1, help="Reason for the rejection")
    renew_rejected_reason = fields.Text(string='Renew Rejected Reason', copy=False, readonly=1,
                                        help="Renew rejected reason")
    date_request = fields.Date(string='Requested Date', required=True, track_visibility='always', readonly=True,
                               help="Requested date",
                               states={'draft': [('readonly', False)]}, default=datetime.now().strftime('%Y-%m-%d'))
    employee = fields.Many2one('hr.employee', string='Employee', required=True, readonly=True, help="Employee",
                               default=lambda self: self.env.user.employee_id.id,
                               states={'draft': [('readonly', False)]})
    purpose = fields.Char(string='Reason', track_visibility='always', readonly=True, help="Reason",
                          states={'draft': [('readonly', False)]})
    
    property_type = fields.Many2one('custody.property.type',string="Property Type")

    custody_name = fields.Many2one('custody.property', string='Property', required=True, readonly=True,
                                   help="Property name",
                                   states={'draft': [('readonly', False)]})

    return_date = fields.Date(string='Return Date', required=False, track_visibility='always', readonly=True,
                              help="Return date",
                              states={'draft': [('readonly', False)]})
    renew_date = fields.Date(string='Renewal Return Date', track_visibility='always',
                             help="Return date for the renewal", readonly=True, copy=False)
    notes = fields.Html(string='Notes')
    renew_return_date = fields.Boolean(default=False, copy=False)
    renew_reject = fields.Boolean(default=False, copy=False)
    state = fields.Selection([('draft', 'Draft'), ('to_approve', 'Waiting For Approval'), ('approved', 'Approved'),
                              ('returned', 'Returned'), ('rejected', 'Refused'),('cancel','Cancelled')], string='Status', default='draft',
                             track_visibility='always')
    mail_send = fields.Boolean(string="Mail Send")
    def get_hr_manager_domain(self):
        return [('id', 'in', self.env.ref('hr.group_hr_manager').users.ids)]
    hr_manager = fields.Many2one('res.users',string="HR Manager",required=True,domain=get_hr_manager_domain)


class HrPropertyType(models.Model):
    _name = "custody.property.type"
    name = fields.Char(string="Name")
    property_count = fields.Integer(string="Total Properties", compute="_compute_property_count")
    
    def _compute_property_count(self):
        for record in self:
            record.property_count = self.env['custody.property'].sudo().search_count([('property_type','=',record.id)])

class HrPropertyName(models.Model):
    """
            Hr property creation model.
            """
    _name = 'custody.property'
    _description = 'Property Name'

    name = fields.Char(string='Property Name', required=True)
    property_type = fields.Many2one('custody.property.type',string="Property Type")
    serial_no = fields.Char(string="Serial No", required=True)
    image = fields.Image(string="Image",
                         help="This field holds the image used for this provider, limited to 1024x1024px")
    image_medium = fields.Binary(
        "Medium-sized image", attachment=True,
        help="Medium-sized image of this provider. It is automatically "
             "resized as a 128x128px image, with aspect ratio preserved. "
             "Use this field in form views or some kanban views.")
    image_small = fields.Binary(
        "Small-sized image", attachment=True,
        help="Small-sized image of this provider. It is automatically "
             "resized as a 64x64px image, with aspect ratio preserved. "
             "Use this field anywhere a small image is required.")
    desc = fields.Html(string='Description', help="Description")
    company_id = fields.Many2one('res.company', 'Company', help="Company",
                                 default=lambda self: self.env.user.company_id)
    property_selection = fields.Selection([('empty', 'No Connection'),
                                           ('product', 'Products')],
                                          default='empty',
                                          string='Property From', help="Select the property")

    product_id = fields.Many2one('product.product', string='Product', help="Product")
    
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
    purchase_price = fields.Monetary(string="Purchase Price")
    def _compute_current_user(self):
        for record in self:
            assigned=False
            for report in record.custody_report_ids:
                if report.state == 'approved':
                    record.current_user = report.employee.id
                    assigned=True
                    break
            if not assigned:
                record.current_user = False
    current_user = fields.Many2one('hr.employee',string="Current User",compute="_compute_current_user")
    is_scrap = fields.Boolean(string="Is Scrap")
    scrap_money = fields.Monetary(string="Scrap Credit")
    scrap_reason = fields.Text(string="Scrap Reason")
    scrap_date = fields.Date(string="Scrap Date")
    def _compute_report_ids(self):
        for record in self:
            record.custody_report_ids = self.env['report.custody'].search([('custody_name','=',record.id)])
    custody_report_ids = fields.One2many('report.custody','custody_name',string="Custody Reports")
    def _compute_repair_ids(self):
        for record in self:
            record.repair_ids = self.env['custody.property.repair'].search([('property_id','=',record.id)])
    repair_ids = fields.One2many('custody.property.repair','property_id',string="Repairs",compute="_compute_repair_ids")


    # def _compute_read_only(self):
    #     """ Use this function to check weather the user has the permission to change the employee"""
    #     res_user = self.env['res.users'].search([('id', '=', self._uid)])
    #     print(res_user.has_group('hr.group_hr_user'))
    #     if res_user.has_group('hr.group_hr_user'):
    #         self.read_only = True
    #     else:
    #         self.read_only = False

    def cancel_requests(self):
        custody_reqs = self.env['hr.custody'].search([('custody_name','=',self.id),('state','in',('draft','to_approve'))])
        if custody_reqs:
            for req in custody_reqs:
                req.write({
                    'state':'cancel'
                })
    def convert_scrap(self):
        custody_reqs = self.env['hr.custody'].search([('custody_name','=',self.id),('state','in',('draft','to_approve'))])
        if custody_reqs:
            raise UserError("You have to cancel all custody requests in Draft and Waiting Approval states before turning a property into scrap")
        custody_reqs = self.env['hr.custody'].search([('custody_name','=',self.id),('state','=','approved')])
        if custody_reqs:
            raise UserError("Approved properties have to be returned before turning into scrap")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Convert to Scrap',
            'res_model': 'property.scrap.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'property_id': self.id,
            }
        }

    def add_repair_record(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Repair Record',
            'res_model': 'property.repair.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'property_id': self.id,
            }
        }
    @api.onchange('property_selection')
    def onchange_property_selection(self):
        if self.property_selection == 'asset':
            asset_obj = self.env['ir.module.module'].search([('name', '=', 'account_asset')])
            if asset_obj.state != 'installed':
                self.asset_true = False
                raise UserError(_('No asset module found. Kindly install the asset module.'))
            else:
                self.asset_true = True

    @api.onchange('product_id')
    def onchange_product(self):
        self.name = self.product_id.name


class HrReturnDate(models.TransientModel):
    """Hr custody contract renewal wizard"""
    _name = 'wizard.return.date'
    _description = 'Hr Custody Name'

    returned_date = fields.Date(string='Renewal Date', required=1)

    # renewal date validation
    @api.constrains('returned_date')
    def validate_return_date(self):
        context = self._context
        custody_obj = self.env['hr.custody'].search([('id', '=', context.get('custody_id'))])
        if self.returned_date <= custody_obj.date_request:
            raise Warning('Please Give Valid Renewal Date')

    def proceed(self):
        context = self._context
        custody_obj = self.env['hr.custody'].search([('id', '=', context.get('custody_id'))])
        custody_obj.write({'renew_return_date': True,
                           'renew_date': self.returned_date,
                           'state': 'to_approve'})
