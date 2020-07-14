from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.modules import get_module_resource
#from odoo.tools import image_colorize, image_resize_image_big
from odoo.tools import *
import base64
import datetime


class PmsFormat(models.Model):
    _name = "pms.format"
    _description = "Property Formats"
    _order = "name"

    name = fields.Char("Name", required=True)
    sample = fields.Char("Sample",
                         compute='get_sample_format',
                         store=True,
                         readonly=True)
    active = fields.Boolean(default=True)
    format_line_id = fields.One2many("pms.format.detail", "format_id",
                                     "Format Line")

    def name_get(self):
        result = []
        for record in self:
            sample = record.sample
            result.append((record.id, sample))
        return result

    @api.model
    def create(self, values):
        return super(PmsFormat, self).create(values)

    @api.depends('format_line_id')
    def get_sample_format(self):
        for record in self:
            f_val = []
            record.sample = ''
            if record.format_line_id:
                for fl in record.mapped('format_line_id'):
                    if fl.value_type == 'fix' and fl.fix_value:
                        f_val.append(fl.fix_value)
                    if fl.value_type == 'digit' and fl.digit_value:
                        for d in range(fl.digit_value):
                            f_val.append(str('x'))
                    if fl.value_type == 'dynamic' and fl.dynamic_value:
                        f_val.append(fl.dynamic_value)
                    if fl.value_type == 'datetime' and fl.datetime_value:
                        f_val.append(fl.datetime_value)
                if f_val:
                    for sm in range(len(f_val)):
                        record.sample += f_val[sm]

    def toggle_active(self):
        for pt in self:
            if not pt.active:
                pt.active = self.active
        super(PmsFormat, self).toggle_active()


    @api.model
    def create(self, values):
        format_id = self.search([('name', '=', values['name'])])
        if format_id:
            raise UserError(_("%s is already existed" % values['name']))
        return super(PmsFormat, self).create(values)

        # if 'name' in values:
        #     sample_id = self.search([('name', '=', values['name'])])
        #     if sample_id:
        #         raise UserError(_("%s is already existed" % values['name']))
        # return super(PmsFormat, self).create(values)
        # format_ids = self.search([('name', '=', values['name'])])
        # for format_id in format_ids:
        #     if format_id:
        #         raise UserError(_("%s is already existed" % values['name']))
        # return super(PmsFormat, self).create(values)

    def write(self, vals):
        format_id = None
        if 'name' in vals:
            sample_id = self.search([('name', '=', vals['name'])])
            if sample_id:
                raise UserError(_("%s is already existed" % vals['name']))
        return super(PmsFormat, self).write(vals)

class PmsFormatDetail(models.Model):
    _name = "pms.format.detail"
    _description = "Property Formats Details"
    _order = "position_order"

    @api.depends(
        'fix_value',
        'digit_value',
        'dynamic_value',
        'datetime_value',
    )
    def get_value_type(self):
        for record in self:
            if record.value_type:
                if record.value_type == 'fix':
                    record.value = record.fix_value
                if record.value_type == 'dynamic':
                    record.value = record.dynamic_value
                if record.value_type == 'digit':
                    record.value = record.digit_value
                if record.value_type == 'datetime':
                    record.value = record.datetime_value

    name = fields.Char("Name", default="New")
    format_id = fields.Many2one("pms.format", "Format")
    position_order = fields.Integer("Position Order",
                                    compute='_get_line_numbers',
                                    store=True,
                                    readonly=False)
    value_type = fields.Selection([('fix', "Fix"), ('dynamic', 'Dynamic'),
                                   ('digit', 'Digit'),
                                   ('datetime', 'Datetime')],
                                  string="Type",
                                  default="")
    fix_value = fields.Char("Fixed Value", store=True)
    digit_value = fields.Integer("Digit Value", store=True)
    dynamic_value = fields.Selection([('unit code', 'unit code'),
                                      ('property code', 'property code'),
                                      ('pos code', 'pos code'),
                                      ('floor code', 'floor code'),
                                      ('floor ref code', 'floor ref code')],
                                     string="Dynamic Value",
                                     store=True)
    datetime_value = fields.Selection([('MM', 'MM'), ('MMM', 'MMM'),
                                       ('YY', 'YY'), ('YYYY', 'YYYY')],
                                      string="Date Value",
                                      store=True)
    value = fields.Char("Value", compute='get_value_type')

    def _get_line_numbers(self):
        for record in self:
            for fmt in record.mapped('format_id'):
                line_no = 1
                for line in fmt.format_line_id:
                    line.position_order = line_no
                    line_no += 1

    @api.model
    def default_get(self, fields_list):
        res = super(PmsFormatDetail, self).default_get(fields_list)
        res.update({
            'position_order':
            len(self._context.get('format_line_id', [])) + 1
        })
        return res

class Users(models.Model):
    _inherit = "res.users"

    property_id = fields.Many2many("property.property",
                                   'property_id',
                                   'user_id',
                                   "property_property_user_rel",
                                   "Property",
                                   store=True,
                                   track_visibility=True)

class Company(models.Model):
    _inherit = "res.company"

    #Guest Profile ID format
    def _default_profile_id_format(self):
        if not self.profile_id_format:
            return self.env.ref('base.main_company').profile_id_format

    #Company Profile ID Format
    def _default_cprofile_id_format(self):
        if not self.cprofile_id_format:
            return self.env.ref('base.main_company').cprofile_id_format

    #Group Profile ID Format
    def _default_gprofile_id_format(self):
        if not self.gprofile_id_format:
            return self.env.ref('base.main_company').gprofile_id_format

    # Confirm ID Format
    def _default_confirm_id_format(self):
        if not self.confirm_id_format:
            return self.env.ref('base.main_company').confirm_id_format


    property_code_len = fields.Integer("Property Code Length",
                                    default=8,
                                    track_visibility=True)
    location_code_len = fields.Integer('Floor Code Length',
                                    track_visibility=True,
                                    default=15)
    building_code_len = fields.Integer('Building Code Length', 
                                    track_visibility=True,
                                    default=30)
    confirm_id_format = fields.Many2one('pms.format',
                                    'Confirm No Format',
                                    default=_default_confirm_id_format, 
                                    track_visibility=True)
    profile_id_format = fields.Many2one('pms.format',
                                    'Profile ID Format',
                                    default=_default_profile_id_format,
                                    track_visibility=True)
    cprofile_id_format = fields.Many2one('pms.format',
                                    'Company Profile ID Format',
                                    default=_default_cprofile_id_format,
                                    track_visibility=True)
    gprofile_id_format = fields.Many2one('pms.format',
                                    'Group Profile ID Format',
                                    default=_default_gprofile_id_format,
                                    track_visibility=True)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def get_company_id(self):
        if not self.company_id:
            return self.env.user.company_id

    company_id = fields.Many2one('res.company', default=get_company_id)
    property_code_len = fields.Integer("Property Code Length",
                                    related="company_id.property_code_len",
                                    readonly=False)
    location_code_len = fields.Integer('Floor Code Length',
                                    related="company_id.location_code_len",
                                    readonly=False)
    building_code_len = fields.Integer('Building Code Length',
                                    related="company_id.building_code_len",
                                    readonly=False)
    confirm_id_format = fields.Many2one('pms.format',
                                    'Confirm No Format',
                                    related="company_id.confirm_id_format", 
                                    track_visibility=True)
    profile_id_format = fields.Many2one('pms.format',
                                    'Guest Profile ID Format',
                                    related="company_id.profile_id_format",
                                    track_visibility=True)
    cprofile_id_format = fields.Many2one('pms.format',
                                    'Company Profile ID Format',
                                    related="company_id.cprofile_id_format",
                                    track_visibility=True)
    gprofile_id_format = fields.Many2one('pms.format',
                                    'Group Profile ID Format',
                                    related="company_id.gprofile_id_format",
                                    track_visibility=True)

    
    @api.onchange('property_code_len')
    def onchange_property_code_len(self):
        if self.property_code_len:
            self.company_id.property_code_len = self.property_code_len

    @api.onchange('location_code_len')
    def onchange_location_code_len(self):
        if self.location_code_len:
            self.company_id.location_code_len = self.location_code_len

    @api.onchange('building_code_len')
    def onchange_building_code_len(self):
        if self.building_code_len:
            self.company_id.building_code_len = self.building_code_len
    
    @api.onchange('confirm_id_format')
    def onchange_confirm_id_format(self):
        if self.confirm_id_format:
            self.company_id.confirm_id_format = self.confirm_id_format

    @api.onchange('profile_id_format')
    def onchange_profile_id_format(self):
        if self.profile_id_format:
            self.company_id.profile_id_format = self.profile_id_format
    
    @api.onchange('cprofile_id_format')
    def onchange_cprofile_id_format(self):
        if self.cprofile_id_format:
            self.company_id.cprofile_id_format = self.cprofile_id_format

    @api.onchange('gprofile_id_format')
    def onchange_gprofile_id_format(self):
        if self.gprofile_id_format:
            self.company_id.gprofile_id_format = self.gprofile_id_format

    

