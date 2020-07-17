import base64
import logging

from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.modules import get_module_resource
from odoo.tools import *
from datetime import datetime, date, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

AVAILABLE_RATETYPE = [
    ('D', 'Daily'),
    ('M', 'Monthly'),
]


# Rate Code Header
class RateCodeHeader(models.Model):
    _name = "ratecode.header"
    _description = "Rate Code Header"

    header_create = fields.Boolean(default=True)
    is_ratecode = fields.Boolean(string='Is ratecode',
                                 compute='_compute_is_ratecode')
    property_id = fields.Many2one('property.property',
                                  string="Property",
                                  required=True,
                                  readonly=True)
    rate_code = fields.Char(string="Rate Code", size=10, required=True)
    ratecode_name = fields.Char(string="Description", required=True)
    start_date = fields.Date(string="Start Date",
                             required=True,
                             default=datetime.today())
    end_date = fields.Date(string="End Date", required=True)
    ratecode_type = fields.Selection(AVAILABLE_RATETYPE,
                                     string="Type",
                                     default='D',
                                     required=True)
    ratecode_details = fields.One2many('ratecode.details',
                                       'ratehead_id',
                                       string="Rate Code Details")
    rate_category_id = fields.Many2one('rate.categories',
                                       string="Rate Categories",
                                       required=True)
    pkg_group_ids = fields.One2many('package.group',
                                    related="property_id.packagegroup_ids")
    pkg_group_id = fields.Many2one('package.group', string="Package")

    _sql_constraints = [(
        'rate_code_unique',
        'UNIQUE(property_id,rate_category_id,rate_code,ratecode_name)',
        'Rate Code already exists! Rate Code Name and Description must be unique!'
    )]

    def _compute_is_ratecode(self):
        self.is_ratecode = True

    def name_get(self):
        result = []
        for record in self:
            result.append(
                (record.id, "{} ({} {})".format(record.rate_code,
                                                record.start_date,
                                                record.end_date)))
        return result

    @api.onchange('start_date', 'end_date')
    @api.constrains('start_date', 'end_date')
    def get_two_date_comp(self):
        for rec in self:
            startdate = rec.start_date
            enddate = rec.end_date
            if startdate and enddate and startdate > enddate:
                raise ValidationError(
                    "End Date cannot be set before Start Date.")

    @api.model
    def create(self, values):
        res = super(RateCodeHeader, self).create(values)

        if res.header_create is True:
            rate_category_id = res.rate_category_id
            property_id = res.property_id
            start_date = res.start_date
            end_date = res.end_date
            rate_code = res.rate_code
            ratecode_name = res.ratecode_name
            create = False

            res.rate_category_id.rate_header_ids._update_property_ratecodeheader(
                rate_category_id, property_id, start_date, end_date, rate_code,
                ratecode_name, create)

        return res


# Rate Code Detail
class RateCodeDetails(models.Model):

    # def default_get_start_date(self):

    #     if self.ratehead_id.ratecode_details:
    #         max_start_date = max(self.ratehead_id.ratecode_details.mapped('end_date'))
    #         if max_start_date:
    #             return max_start_date
    #     else:
    #         return datetime.today()

    _name = "ratecode.details"
    _description = "Rate Code Details"

    sequence = fields.Integer('Sequence', default=1)
    ratehead_id = fields.Many2one('ratecode.header', string="Rate Code Header")
    property_id = fields.Many2one('property.property',
                                  string="Property",
                                  readonly=True)
    season_code = fields.Char(string="Season", size=10, required=True)
    roomtype_ids = fields.Many2many("room.type",
                                    related="property_id.roomtype_ids")
    roomtype_id = fields.Many2many('room.type',
                                   string="Room Type",
                                   store=True,
                                   domain="[('id', '=?', roomtype_ids)]",
                                   required=True)
    # roomtype_id = fields.One2many('room.type',
    #                               'rate_id',
    #                               string="Room Type",
    #                               store=True,
    #                               domain="[('id', '=?', roomtype_ids)]",
    #                               required=True)
    start_date = fields.Date(string="Start Date",
                             required=True,
                             default=datetime.today())
    end_date = fields.Date(string="End Date", required=True)
    transaction_id = fields.Many2one(
        'transaction.transaction',
        string='Transaction',
        domain=
        "[('property_id', '=?', property_id), ('allowed_pkg', '=?', True)]",
        required=True)
    normal_price1 = fields.Float(string="1 Adult")
    normal_price2 = fields.Float(string="+2 Adult")
    normal_price3 = fields.Float(string="+3 Adult")
    normal_price4 = fields.Float(string="+4 Adult")
    normal_extra = fields.Float(string="Extra")
    weekend_price1 = fields.Float(string="Weekend 1 Adult")
    weekend_price2 = fields.Float(string="+2 Adult")
    weekend_price3 = fields.Float(string="+3 Adult")
    weekend_price4 = fields.Float(string="+4 Adult")
    weekend_extra = fields.Float(string="Extra")
    special_price1 = fields.Float(string="Special 1 Adult")
    special_price2 = fields.Float(string="+2 Adult")
    special_price3 = fields.Float(string="+3 Adult")
    special_price4 = fields.Float(string="+4 Adult")
    special_extra = fields.Float(string="Extra")
    extra_bed = fields.Float(string="Extra Bed")
    adult_bf = fields.Float(string="Adult Breakfast")
    child_bf = fields.Float(string="Child Breakfast")
    package_id = fields.Char(string="Package")
    discount_percent = fields.Float(string="Discount Percentage", default=10.0)
    discount_amount = fields.Float(string="Discount Amount", default=50.0)

    def name_get(self):
        result = []
        for record in self:
            result.append(
                (record.id,
                 "{} | ({} {}) | 1Pax-{}| 2Pax-{}| 3Pax-{}| 4Pax-{}| Extra-{}".
                 format(record.season_code, record.start_date, record.end_date,
                        record.normal_price1, record.normal_price2,
                        record.normal_price3, record.normal_price4,
                        record.normal_extra)))
        return result

    @api.onchange('start_date', 'end_date')
    @api.constrains('start_date', 'end_date')
    def get_two_date_comp(self):
        for record in self:
            startdate = record.start_date
            enddate = record.end_date
            if startdate and enddate and startdate > enddate:
                raise ValidationError(
                    "End Date cannot be set before Start Date.")

    @api.onchange('start_date', 'end_date', 'roomtype_id')
    @api.constrains('start_date', 'end_date', 'roomtype_id')
    def check_date_range(self):

        for current in self:
            count = 0
            for rec in current.ratehead_id.ratecode_details:
                if rec.start_date and rec.end_date and current.start_date and current.end_date:
                    if current.start_date <= rec.end_date and current.end_date >= rec.start_date:
                        for s_roomtype in current.roomtype_id:
                            if s_roomtype._origin.id in rec.roomtype_id.ids:
                                count += 1
                                break
            if count > 1:
                raise ValidationError(
                    _("One of your room type have overlapping date range"))

    @api.onchange('start_date')
    def get_start_date(self):

        tmp_end_date = date(1000, 1, 11)
        prv_ratecode_details = self.env['ratecode.details']
        for rec in self.ratehead_id.ratecode_details:
            if not self.start_date:
                end_date = rec.end_date
                if end_date:
                    if end_date > tmp_end_date:
                        tmp_end_date = end_date
                        prv_ratecode_details = rec
        if prv_ratecode_details:
            self.start_date = prv_ratecode_details.end_date + timedelta(days=1)
        elif not prv_ratecode_details and not self.start_date:
            self.start_date = datetime.today()

    @api.onchange('start_date', 'end_date')
    @api.constrains('start_date', 'end_date')
    def check_header_date_range(self):

        for current in self:
            header_start_date = current.ratehead_id.start_date
            header_end_date = current.ratehead_id.end_date

            cur_start_date = current.start_date
            cur_end_date = current.end_date

            if header_end_date and header_start_date and cur_start_date and cur_end_date:
                # if not (cur_start_date < header_end_date and cur_end_date > header_start_date):
                #     raise ValidationError(_("Season Code date range must be within Rate Code date range"))
                if cur_start_date < header_start_date or cur_end_date > header_end_date:
                    raise ValidationError(
                        _("Season Code date range must be within Rate Code date range"
                          ))


# Rate Code Categories
class RateCategories(models.Model):
    _name = "rate.categories"
    _description = "Rate Categories"
    _order = 'sequence, code'

    is_rate_category = fields.Boolean(string='Is Rate Category',
                                      compute='_compute_is_rate_category')
    active = fields.Boolean(string="Active",
                            default=True,
                            track_visibility=True)
    sequence = fields.Integer(default=1)
    code = fields.Char(string="Code", size=10, required=True)
    categories = fields.Char(string="Description", required=True)
    start_date = fields.Date(string="Start Date",
                             required=True,
                             default=datetime.today())
    end_date = fields.Date(string="End Date")
    rate_header_ids = fields.One2many('ratecode.head',
                                      'rate_category_id',
                                      string="Rate Codes",
                                      required=True)
    terminate_end_date = fields.Date(string="Terminate End Date",
                                     compute='get_terminate_end_date',
                                     store=True)

    def _compute_is_rate_category(self):
        self.is_rate_category = True

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.code,
                                                       record.start_date)))
        return result

    def unlink(self):
        ratecode_head_objs = self.env['ratecode.head']

        for rec in self:
            ratecode_head_objs += self.env['ratecode.head'].search([
                ('rate_category_id', '=', rec.id)
            ])
            ratecode_head_objs.unlink()

        res = super(RateCategories, self).unlink()
        return res

    @api.depends('rate_header_ids')
    def get_terminate_end_date(self):
        tmp_end_date = date(1000, 1, 11)
        rate_header_obj = self.env['ratecode.head']
        for rec in self.rate_header_ids:
            if rec.end_date and rec.end_date > tmp_end_date:
                tmp_end_date = rec.end_date
                rate_header_obj = rec
        if rate_header_obj:
            self.terminate_end_date = rate_header_obj.end_date

    # @api.constrains('start_date')
    # def check_start_date(self):
    #     for rec in self:
    #         start_date = rec.start_date
    #         if start_date:
    #             if datetime.strptime(str(start_date),
    #                                  DEFAULT_SERVER_DATE_FORMAT).date(
    #                                  ) < datetime.now().date():
    #                 raise ValidationError(
    #                     _('Start date should be greater than or equal to the current date.'
    #                       ))
    #                 rec.start_date = datetime.now().date()


# Rate Code Header for Rate Categories
class RateCodeHead(models.Model):
    _name = "ratecode.head"
    _description = "Rate Code"

    head_create = fields.Boolean(default=True)
    rate_code = fields.Char(string="Rate Code", size=10, required=True)
    ratecode_name = fields.Char(string="Description", required=True)
    start_date = fields.Date(string="Start Date",
                             required=True,
                             default=datetime.today())
    end_date = fields.Date(string="End Date", required=True)
    rate_category_id = fields.Many2one('rate.categories',
                                       string="Rate Categories")
    property_ids = fields.Many2many("property.property",
                                    store=True,
                                    track_visibility=True)

    def _update_property_ratecodeheader(self, rate_category_id, property_id,
                                        start_date, end_date, rate_code,
                                        ratecode_name, create):
        if create is True:
            vals = []
            vals.append((
                0,
                0,
                {
                    'rate_category_id': rate_category_id.id,
                    'property_id': property_id.id,
                    'start_date': start_date,
                    'end_date': end_date,
                    'rate_code': rate_code,
                    'ratecode_name': ratecode_name,
                    'ratecode_type': 'D',
                    'header_create': False,
                    # 'rate_category_id': res.rate_category_id.id,
                }))
            property_id.update({'ratecodeheader_ids': vals})

        if create is False:
            rate_category_objs = self.env['rate.categories'].search([
                ('id', '=', rate_category_id.id)
            ])

            for rate_category_obj in rate_category_objs:
                same_rate_code_objs = rate_category_obj.rate_header_ids.filtered(
                    lambda x: x.rate_code == rate_code and x.ratecode_name ==
                    ratecode_name)

                if same_rate_code_objs:
                    if end_date > same_rate_code_objs.end_date:
                        same_rate_code_objs.update({
                            'end_date':
                            end_date,
                            'property_ids': [(4, property_id.id)]
                        })
                    else:
                        same_rate_code_objs.update(
                            {'property_ids': [(4, property_id.id)]})

                else:
                    vals = []
                    vals.append((0, 0, {
                        'rate_category_id': rate_category_id.id,
                        'property_ids': [(4, property_id.id)],
                        'start_date': start_date,
                        'end_date': end_date,
                        'rate_code': rate_code,
                        'ratecode_name': ratecode_name,
                        'head_create': False,
                    }))
                    rate_category_obj.update({'rate_header_ids': vals})

    @api.model
    def create(self, values):
        res = super(RateCodeHead, self).create(values)

        if res.property_ids and res.head_create is True:
            for record in res.property_ids:
                rate_category_id = res.rate_category_id
                property_id = record
                start_date = res.start_date
                end_date = res.end_date
                rate_code = res.rate_code
                ratecode_name = res.ratecode_name
                create = True
                res._update_property_ratecodeheader(rate_category_id,
                                                    property_id, start_date,
                                                    end_date, rate_code,
                                                    ratecode_name, create)

        return res

    def write(self, values):
        res = super(RateCodeHead, self).write(values)

        if 'property_ids' in values.keys():
            head_create = values.get('head_create')
            # if not head_create:
            properties = self.property_ids
            rate_category_id = self.rate_category_id
            rate_code = self.rate_code
            ratecode_name = self.ratecode_name
            for property_id in properties:
                ratecode_header_objs = self.env['ratecode.header'].search([
                    ('rate_category_id', '=', rate_category_id.id),
                    ('rate_code', '=', rate_code),
                    ('ratecode_name', '=', ratecode_name),
                    ('property_id', '=', property_id.id)
                ])

                if not ratecode_header_objs:
                    property_id = property_id
                    start_date = self.start_date
                    end_date = self.end_date
                    create = True
                    self._update_property_ratecodeheader(
                        rate_category_id, property_id, start_date, end_date,
                        rate_code, ratecode_name, create)

        return res

    def unlink(self):
        ratecode_header_objs = self.env['ratecode.header']

        for rec in self:
            ratecode_header_objs += self.env['ratecode.header'].search([
                ('rate_code', '=', rec.rate_code),
                ('ratecode_name', '=', rec.ratecode_name)
            ])
            ratecode_header_objs.unlink()

        res = super(RateCodeHead, self).unlink()
        return res


# Season Code Categories
# class SeasonCode(models.Model):
#     _name = "season.code"
#     _description = "Season Code"
#     _order = 'sequence, code'

#     active = fields.Boolean(string="Active", default=True, track_visibility=True)
#     sequence = fields.Integer(default=1)
#     code = fields.Char(string="Code", size=10, required=True)
#     seasons = fields.Char(string="Description", required=True)
#     start_date = fields.Date(string="Start Date", required=True)
#     end_date = fields.Date(string="End Date", required=True)
#     # property_ids = fields.Many2many("property.property",
#     #                                'property_id',
#     #                                'season_id',
#     #                                "property_property_rate_season_rel",
#     #                                "Property",
#     #                                store=True,
#     #                                track_visibility=True)

#     def name_get(self):
#         result = []
#         for record in self:
#             result.append(
#                 (record.id, "{} ({} - {})".format(record.code,
#                                              record.start_date,record.end_date)))
#         return result