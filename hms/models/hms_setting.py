from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.modules import get_module_resource
#from odoo.tools import image_colorize, image_resize_image_big
from odoo.tools import *
import base64
from datetime import datetime
from odoo.osv import expression
import logging
_logger = logging.getLogger(__name__)


class Country(models.Model):
    _inherit = "res.country"

    code = fields.Char(
        string='Country Code',
        size=3,
        help=
        'The ISO country code in three chars. \nYou can use this field for quick search.'
    )

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.name,
                                                       record.code)))
        return result


class Bank(models.Model):
    _inherit = 'res.bank'

    property_id = fields.Many2one('property.property',
                                  string="Property",
                                  required=True,
                                  readonly=True)
    logo = fields.Binary(string='Logo', attachment=True, store=True)
    bic = fields.Char('Switch Code',
                      index=True,
                      track_visibility=True,
                      help="Sometimes called BIC or Swift.")
    branch = fields.Char("Branch Name",
                         index=True,
                         help="Sometimes called BIC or Swift.")

    _sql_constraints = [('name_unique', 'unique(name)',
                         'Your name is exiting in the database.')]


class HMSCity(models.Model):
    _name = "hms.city"
    _description = "City"
    _order = "code,name"

    state_id = fields.Many2one("res.country.state",
                               "State Name",
                               required=True,
                               track_visibility=True)
    name = fields.Char("City Name", required=True, track_visibility=True)
    code = fields.Char("City Code", required=True, track_visibility=True)
    _sql_constraints = [('code_unique', 'unique(code)',
                         'City Code is already existed.')]


class HMSTownship(models.Model):
    _name = "hms.township"
    _description = "Township"
    _order = "code,name"

    name = fields.Char("Name", required=True, track_visibility=True)
    code = fields.Char("Code", required=True, track_visibility=True)
    city_id = fields.Many2one("hms.city",
                              "City",
                              ondelete='cascade',
                              required=True,
                              track_visibility=True)
    _sql_constraints = [('code_unique', 'unique(code)',
                         'Township Code is already existed.')]


class HMSCountry(models.Model):
    _name = "hms.country"
    _description = "Country"

    name = fields.Char("Country Name", required=True, track_visibility=True)
    code = fields.Char("Country Code",
                       size=3,
                       required=True,
                       track_visibility=True)
    _sql_constraints = [('code_unique', 'unique(code)',
                         'Country Code is already existed.')]


class Nationality(models.Model):
    _description = "Country state"
    _name = 'hms.nationality'
    _order = 'code'

    name = fields.Char(
        string='Nationality Name',
        required=True,
        help=
        'Administrative divisions of a country. E.g. Fed. State, Departement, Canton'
    )
    code = fields.Char(string='Nationality Code',
                       help='The nationality code.',
                       required=True,
                       size=3)

    _sql_constraints = [('name_code_uniq', 'unique(code)',
                         'The code of the state must be unique by country !')]

    @api.model
    def _name_search(self,
                     name,
                     args=None,
                     operator='ilike',
                     limit=100,
                     name_get_uid=None):
        args = args or []

        if operator == 'ilike' and not (name or '').strip():
            first_domain = []
            domain = []
        else:
            first_domain = [('code', '=ilike', name)]
            domain = [('name', operator, name)]

        first_state_ids = self._search(
            expression.AND([first_domain, args]),
            limit=limit,
            access_rights_uid=name_get_uid) if first_domain else []
        state_ids = first_state_ids + [
            state_id
            for state_id in self._search(expression.AND([domain, args]),
                                         limit=limit,
                                         access_rights_uid=name_get_uid)
            if not state_id in first_state_ids
        ]
        return models.lazy_name_get(
            self.browse(state_ids).with_user(name_get_uid))

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.code,
                                                       record.name)))
        return result


class Passport(models.Model):
    _name = "hms.passport"
    _description = "PassPort"

    profile_id = fields.Many2one('res.partner',
                                 string="Profile",
                                 required=True)
    passport = fields.Char(string="Passport", required=True)
    issue_date = fields.Date(string="Issue Date", required=True)
    expire_date = fields.Date(string="Expired Date")
    country_id = fields.Many2one('res.country', string="Country")
    nationality = fields.Many2one('hms.nationality', string="Nationality")
    #image1 = fields.Many2many('ir.attachment', string="Image")
    image1 = fields.Binary(string="Photo 1", attachemtn=True, store=True)
    image2 = fields.Binary(string="Photo 2", attachemtn=True, store=True)
    image3 = fields.Binary(string="Photo 3", attachemtn=True, store=True)
    image4 = fields.Binary(string="Photo 4", attachemtn=True, store=True)
    note = fields.Text(string="Internal Note")
    active = fields.Boolean(string="Active",
                            default=True,
                            track_visibility=True)

    _sql_constraints = [('passport_unique', 'UNIQUE(passport)',
                         'Your passport is exiting in the database.')]

    # Activate the latest passport
    @api.constrains('active')
    def _change_active_status(self):
        for record in self:
            if record.active:
                record_list = self.env['hms.passport'].search([('id', '!=',
                                                                self.id)])
                record.profile_id.image_1920 = record.image1
                for rec in record_list:
                    rec.active = False

    @api.onchange('issue_date', 'expire_date')
    @api.constrains('issue_date', 'expire_date')
    def get_two_date_comp(self):
        issue_date = self.issue_date
        expire_date = self.expire_date
        if issue_date and expire_date and issue_date > expire_date:
            raise ValidationError("End Date cannot be set before Start Date.")

    @api.onchange('country_id')
    def _change_default_nationality(self):
        for record in self:
            if record.country_id:
                _logger.info(record.country_id)
                record.nationality = self.env['hms.nationality'].search([
                    ('code', '=', record.country_id.code)
                ]).id


class Contract(models.Model):
    _name = "hms.contract"
    _description = "Contract"

    profile_id = fields.Char(string="Profile")
    name = fields.Char(string="Name", required=True)
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    note = fields.Text(string="Internal Note")
    file = fields.Binary(string="File")

    @api.onchange('start_date', 'end_date')
    @api.constrains('start_date', 'end_date')
    def get_two_date_comp(self):
        start_date = self.start_date
        end_date = self.end_date
        if start_date and end_date and start_date > end_date:
            raise ValidationError("End Date cannot be set before Start Date.")


class HMSCompanyCategory(models.Model):
    _name = "hms.company.category"
    _description = "Company Category"
    _order = 'ordinal_no,code,name'

    name = fields.Char("Description", required=True, track_visibility=True)
    # type = fields.Selection(
    #     string = 'Type',
    #     selection=[('guest', 'Guest'), ('company', 'Company'),('group','Group')],
    #      compute='_compute_type',
    #     inverse='_write_type',
    # )
    type = fields.Selection(
        string='Type',
        selection=[('agent', 'Travel Agent'), ('other', 'Other')],
        required=True,
    )
    code = fields.Char("Code", track_visibility=True, size=3)
    ordinal_no = fields.Integer("Ordinal No", track_visibility=True)
    active = fields.Boolean(default=True, track_visibility=True)

    def toggle_active(self):
        for ct in self:
            if not ct.active:
                ct.active = self.active
        super(HMSCompanyCategory, self).toggle_active()

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.name,
                                                       record.code)))
        return result

    # Create Function
    @api.model
    def create(self, values):
        # _logger.info(values)
        res = super(HMSCompanyCategory, self).create(values)
        padding = self.env.user.company_id.cprofile_id_format.format_line_id.filtered(
            lambda x: x.value_type == "digit")
        self.env['ir.sequence'].create({
            'name': res.code,
            'code': res.code,
            'padding': padding.digit_value,
            'company_id': False,
            'use_date_range': True,
        })
        return res

    def unlink(self):
        sequence_objs = self.env['ir.sequence']
        for rec in self:
            sequence_objs += self.env['ir.sequence'].search([('code', '=',
                                                              rec.code)])
        sequence_objs.unlink()
        res = super(HMSCompanyCategory, self).unlink()
        return res


class HMSGuestCategory(models.Model):
    _name = "hms.guest.category"
    _description = "Guest Categorys"
    _order = 'ordinal_no,code,name'

    name = fields.Char("Description", required=True, track_visibility=True)
    code = fields.Char("Code", track_visibility=True, size=3)
    ordinal_no = fields.Integer("Ordinal No", track_visibility=True)
    active = fields.Boolean(default=True, track_visibility=True)

    def toggle_active(self):
        for ct in self:
            if not ct.active:
                ct.active = self.active
        super(HMSGuestCategory, self).toggle_active()

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.name,
                                                       record.code)))
        return result


class Company(models.Model):
    _inherit = "res.company"
    _description = 'Companies'
    _order = 'sequence, name'

    code = fields.Char(string="Company Code", size=3, required=True)
    city = fields.Many2one("hms.city",
                           "City Name",
                           compute='_compute_address',
                           inverse='_inverse_city',
                           track_visibility=True,
                           ondelete='cascade')
    township = fields.Many2one("hms.township",
                               "Township Name",
                               inverse='_inverse_township',
                               track_visibility=True,
                               ondelete='cascade')
    company_channel_type = fields.Many2one(
        'hms.company.category',
        string="CRM Type",
        track_visibility=True,
    )

    _sql_constraints = [('name_unique', 'unique(name)',
                         'Your name is exiting in the database.')]

    def _get_company_address_fields(self, partner):
        return {
            'street': partner.street,
            'street2': partner.street2,
            'township': partner.township,
            'city': partner.city_id,
            'zip': partner.zip,
            'state_id': partner.state_id,
            'country_id': partner.country_id,
        }

    def _inverse_township(self):
        for company in self:
            company.partner_id.township = company.township

    @api.model
    def create(self, vals):
        crm_type = vals.get('company_channel_type')
        # crm_type = self.env['hms.company.category'].search([('id','=',crm_type)])
        if not vals.get('favicon'):
            vals['favicon'] = self._get_default_favicon()
        if not vals.get('name') or vals.get('partner_id'):
            self.clear_caches()
            return super(Company, self).create(vals)
        partner = self.env['res.partner'].create({
            'name': vals['name'],
            'is_company': True,
            'image_1920': vals.get('logo'),
            'email': vals.get('email'),
            'phone': vals.get('phone'),
            'website': vals.get('website'),
            'vat': vals.get('vat'),
            'company_channel_type': crm_type,
            'company_type': 'company',
        })
        # compute stored fields, for example address dependent fields
        partner.flush()
        vals['partner_id'] = partner.id
        self.clear_caches()
        company = super(Company, self).create(vals)
        # The write is made on the user to set it automatically in the multi company group.
        self.env.user.write({'company_ids': [(4, company.id)]})

        # Make sure that the selected currency is enabled
        if vals.get('currency_id'):
            currency = self.env['res.currency'].browse(vals['currency_id'])
            if not currency.active:
                currency.write({'active': True})
        return company


# Create Partner Title
class PartnerTitle(models.Model):
    _inherit = 'res.partner.title'
    _order = 'name'
    _description = 'Partner Title'

    gender = fields.Selection(string='Gender',
                              selection=[('male', 'Male'),
                                         ('female', 'Female'),
                                         ('other', 'Other')],
                              track_visibility=True)


# Create Partner
class Partner(models.Model):
    _inherit = "res.partner"

    # def get_property_id(self):
    #     if not self.property_id:
    #         property_id = None
    #         if self.env.user.property_id:
    #             # raise UserError(_("Please set property in user setting."))

    #             property_id = self.env.user.property_id[0]
    #         return property_id or 1

    city_id = fields.Many2one("hms.city", "City Name", track_visibility=True)
    company_type = fields.Selection(string='Company Type',
                                    selection=[('guest', 'Guest'),
                                               ('person', 'Contact'),
                                               ('group', 'Group'),
                                               ('company', 'Company')],
                                    compute='_compute_company_type',
                                    inverse='_write_company_type',
                                    track_visibility=True)
    # New Field
    dob = fields.Date('Date of Birth')
    child_ids = fields.One2many('res.partner',
                                'parent_id',
                                string='Contacts',
                                track_visibility=True,
                                domain=[('is_company', '!=', True)])
    company_channel_type = fields.Many2one('hms.company.category',
                                           string="CRM Type",
                                           track_visibility=True)
    guest_channel_type = fields.Many2one('hms.guest.category',
                                         string="Guest Type",
                                         track_visibility=True)
    township = fields.Many2one('hms.township',
                               "Township",
                               track_visibility=True)
    property_id = fields.Many2one(
        "property.property", track_visibility=True)  #default=get_property_id,
    property_ids = fields.Many2many("property.property", track_visibility=True)
    is_from_hms = fields.Boolean(string="Is from HMS",
                                 default=False,
                                 help="Check if creation is from HMS System")
    is_guest = fields.Boolean(string='Is a Guest',
                              default=False,
                              help="Check if the company type is a Guest")
    is_group = fields.Boolean(string='Is a Group',
                              default=False,
                              help="Check if the company type is a Group")
    is_guest_exists = fields.Boolean(string="Is Guest Exists",
                                     compute='_compute_is_guest_exists')
    first_name = fields.Char(string="First Name",
                             track_visibility=True,
                             store=True)
    middle_name = fields.Char(string="Middle Name", track_visibility=True)
    last_name = fields.Char(string="Last Name", track_visibility=True)
    dob = fields.Date(string="Date of Birth", track_visibility=True)
    nationality_id = fields.Many2one('hms.nationality',
                                     string="Nationality",
                                     track_visibility=True)
    gender = fields.Selection(
        string='Gender',
        selection=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        default='male',
        track_visibility=True,
    )
    nrc_card = fields.Char(string="NRC", track_visibility=True)
    father = fields.Char(string="Father", track_visibility=True)
    passport_id = fields.One2many('hms.passport',
                                  'profile_id',
                                  string="Passport",
                                  track_visibility=True,
                                  context={'active_test': False})
    country_id = fields.Many2one('res.country',
                                 string="Country",
                                 track_visibility=True)
    ratecode_id = fields.Many2one('rate.code',
                                  "Rate Code",
                                  track_visibility=True)
    blacklist = fields.Boolean(default=False, track_visibility=True)
    message = fields.Text(string="Message", track_visibility=True)
    group_code = fields.Char(string="Group Code", track_visibility=True)
    group_name = fields.Char(string="Group Name", track_visibility=True)
    contract_ids = fields.One2many('hms.contract',
                                   'profile_id',
                                   string="Contract",
                                   track_visibility=True)
    ar_no = fields.Char(string="AR NO.")
    profile_no = fields.Char(string="Profile NO.")  # compute="get_profile_no"
    no_of_visit = fields.Integer(string="Number of Visit")
    total_nights = fields.Integer(string="Total Nights")
    room_revenue = fields.Float(string="Room Revenue")
    fb_revenue = fields.Float(string="F&B Revenue")
    ms_revenue = fields.Float(string="MS Revenue")
    allotment_id = fields.Char(striing="Allotment")
    image_1920 = fields.Binary(attachment=True)
    passport_image = fields.Binary(store=True,
                                   attachment=True,
                                   compute='_compute_passport_image')

    def _compute_is_guest_exists(self):
        self.is_guest_exists = True

    # Company Type Radion Button Action
    @api.depends('is_company', 'is_guest', 'is_group')
    def _compute_company_type(self):
        for partner in self:
            if partner.is_company or self._context.get(
                    'default_company_type') == 'company':
                partner.company_type = 'company'
                partner.is_company = True
            elif partner.is_guest or self._context.get(
                    'default_company_type') == 'guest':
                partner.company_type = 'guest'
                partner.is_guest = True
            elif partner.is_group or self._context.get(
                    'default_company_type') == 'group':
                partner.company_type = 'group'
                partner.is_group = True
            else:
                partner.company_type = 'person'

    def _write_company_type(self):
        for partner in self:
            partner.is_company = partner.company_type == 'company'
            partner.is_guest = partner.company_type == 'guest'
            partner.is_group = partner.company_type == 'group'

    @api.onchange('company_type')
    def onchange_company_type(self):
        if self.company_type == 'company':
            self.is_company = True
            self.is_guest = False
            self.is_group = False
        elif self.company_type == 'guest':
            self.is_company = False
            self.is_guest = True
            self.is_group = False
        elif self.company_type == 'group':
            self.is_company = False
            self.is_guest = False
            self.is_group = True
        elif self.company_type == 'person':
            self.is_company = False
            self.is_guest = False
            self.is_group = False

    @api.onchange('first_name', 'middle_name', 'last_name', 'group_code')
    def onchange_name(self):
        firstname = ""
        middlename = ""
        lastname = ""
        group_code = ""
        for record in self:
            if record.first_name:
                firstname = record.first_name + ' '
            if record.middle_name:
                middlename = record.middle_name + ' '
            if record.last_name:
                lastname = record.last_name
            if record.group_code:
                group_code = record.group_code
            record.name = firstname + middlename + lastname + group_code

    @api.onchange('title', 'gender')
    def onchange_title_gender(self):
        for partner in self:
            if partner.title.gender:
                partner.gender = partner.title.gender
            else:
                partner.gender = 'male'

    # @api.onchange('group_code')
    # def onchange_name(self):
    #     group_code = ""
    #     for record in self:
    #         if record.group_code:
    #             group_code = record.group_code
    #         record.name=group_code

    # Profile No Generated
    def generate_profile_no(self, company_type, property_id, crm_type):
        pf_no = ''

        if company_type == 'guest':
            if self.env.user.company_id.profile_id_format:
                format_ids = self.env['pms.format.detail'].search(
                    [('format_id', '=',
                      self.env.user.company_id.profile_id_format.id)],
                    order='position_order asc')
            val = []
            for ft in format_ids:
                if ft.value_type == 'fix':
                    val.append(ft.fix_value)
                if ft.value_type == 'digit':
                    sequent_ids = self.env['ir.sequence'].search([
                        ('code', '=',
                         self.env.user.company_id.profile_id_format.code)
                    ])
                    sequent_ids.write({'padding': ft.digit_value})
                if ft.value_type == 'datetime':
                    mon = yrs = ''
                    if ft.datetime_value == 'MM':
                        mon = datetime.today().month
                        val.append(mon)
                    if ft.datetime_value == 'MMM':
                        mon = datetime.today().strftime('%b')
                        val.append(mon)
                    if ft.datetime_value == 'YY':
                        yrs = datetime.today().strftime("%y")
                        val.append(yrs)
                    if ft.datetime_value == 'YYYY':
                        yrs = datetime.today().strftime("%Y")
                        val.append(yrs)
            space = []
            p_no_pre = ''
            if len(val) > 0:
                for l in range(len(val)):
                    p_no_pre += str(val[l])
            p_no = ''
            p_no += self.env['ir.sequence'].\
                    next_by_code('guest.format') or 'New'
            # next_by_code(self.env.user.company_id.profile_id_format.code) or 'New'
            pf_no = p_no_pre + p_no

        elif company_type == 'company':
            if self.env.user.company_id.cprofile_id_format:
                format_ids = self.env['pms.format.detail'].search(
                    [('format_id', '=',
                      self.env.user.company_id.cprofile_id_format.id)],
                    order='position_order asc')
            val = []
            for ft in format_ids:
                if ft.value_type == 'dynamic':
                    if crm_type.code and ft.dynamic_value == 'company type code':
                        val.append(crm_type.code)
                if ft.value_type == 'fix':
                    val.append(ft.fix_value)
                if ft.value_type == 'digit':
                    sequent_ids = self.env['ir.sequence'].search([
                        ('code', '=', crm_type.code)
                    ])
                    sequent_ids.write({'padding': ft.digit_value})
                if ft.value_type == 'datetime':
                    mon = yrs = ''
                    if ft.datetime_value == 'MM':
                        mon = datetime.today().month
                        val.append(mon)
                    if ft.datetime_value == 'MMM':
                        mon = datetime.today().strftime('%b')
                        val.append(mon)
                    if ft.datetime_value == 'YY':
                        yrs = datetime.today().strftime("%y")
                        val.append(yrs)
                    if ft.datetime_value == 'YYYY':
                        yrs = datetime.today().strftime("%Y")
                        val.append(yrs)
            space = []
            p_no_pre = ''
            if len(val) > 0:
                for l in range(len(val)):
                    p_no_pre += str(val[l])
            p_no = ''
            p_no += self.env['ir.sequence'].\
                    next_by_code(crm_type.code) or 'New'
            pf_no = p_no_pre + p_no

        return pf_no

    # Create Function
    @api.model
    def create(self, values):

        values['is_from_hms'] = True
        company_type = values.get('company_type')
        property_id = values.get('property_id')
        property_id = self.env['property.property'].search([('id', '=',
                                                             property_id)])
        crm_type = values.get('company_channel_type')
        crm_type = self.env['hms.company.category'].search([('id', '=',
                                                             crm_type)])

        if company_type == 'company' or company_type == 'guest':
            pf_no = self.generate_profile_no(company_type, property_id,
                                             crm_type)
            values.update({'profile_no': pf_no})

        if company_type == 'group':
            if property_id:
                if property_id.gprofile_id_format:
                    format_ids = self.env['pms.format.detail'].search(
                        [('format_id', '=', property_id.gprofile_id_format.id)
                         ],
                        order='position_order asc')
                val = []
                for ft in format_ids:
                    if ft.value_type == 'dynamic':
                        if property_id.code and ft.dynamic_value == 'property code':
                            val.append(property_id.code)
                    if ft.value_type == 'fix':
                        val.append(ft.fix_value)
                    if ft.value_type == 'digit':
                        sequent_ids = self.env['ir.sequence'].search([
                            ('code', '=', property_id.code +
                             property_id.gprofile_id_format.code)
                        ])
                        sequent_ids.write({'padding': ft.digit_value})
                    if ft.value_type == 'datetime':
                        mon = yrs = ''
                        if ft.datetime_value == 'MM':
                            mon = datetime.today().month
                            val.append(mon)
                        if ft.datetime_value == 'MMM':
                            mon = datetime.today().strftime('%b')
                            val.append(mon)
                        if ft.datetime_value == 'YY':
                            yrs = datetime.today().strftime("%y")
                            val.append(yrs)
                        if ft.datetime_value == 'YYYY':
                            yrs = datetime.today().strftime("%Y")
                            val.append(yrs)
                space = []
                p_no_pre = ''
                if len(val) > 0:
                    for l in range(len(val)):
                        p_no_pre += str(val[l])
                p_no = ''
                p_no += self.env['ir.sequence'].\
                        next_by_code(property_id.code+property_id.gprofile_id_format.code) or 'New'
                pf_no = p_no_pre + p_no
                values.update({'profile_no': pf_no})

            else:
                raise ValidationError(
                    "Select Property or Create Property First!")

        # values.update({'profile_no':pf_no})

        company_objs = self.env['res.company']
        res = super(Partner, self).create(values)
        _logger.info(res)
        if crm_type.type == 'agent':
            company_objs = self.env['res.company'].create({
                'name': res.name,
                'street': res.street,
                'street2': res.street2,
                'zip': res.zip,
                'city': res.city,
                'state_id': res.state_id,
                'bank_ids': res.bank_ids,
                'email': res.email,
                'phone': res.phone,
            })

            company_objs.partner_id.active = False

        user_objs = self.env['res.users']
        if company_type == 'person':

            self.env['res.users'].create({
                'login': res.name,
                'name': res.name,
                'email': res.email,
                # 'company_id' : res.company_id,
                'partner_id': res.id,
            })
            # user_objs.partner_id.active=False

        return res

    # write function
    def write(self, values):
        res = super(Partner, self).write(values)

        if 'company_type' in values.keys(
        ) or 'company_channel_type' in values.keys():
            crm_type = self.company_channel_type
            # company_type = values.get('company_type')
            company_type = self.company_type
            property_id = self.property_id
            pf_no = self.generate_profile_no(company_type, property_id,
                                             crm_type)
            if pf_no:
                #values.update({'profile_no':pf_no})
                self.profile_no = pf_no
        return res


# Crete Currency
class HMSCurrency(models.Model):
    _name = "hms.currency"
    _description = "Currency"

    name = fields.Char("Name", required=True, track_visibility=True)
    symbol = fields.Char("Symbol", required=True, track_visibility=True)
    status = fields.Boolean("Active", track_visibility=True)

    def action_status(self):
        for record in self:
            if record.status is True:
                record.status = False
            else:
                record.status = True
