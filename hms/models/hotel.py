import re
import logging
from odoo.osv import expression
from psycopg2 import IntegrityError
from odoo.tools.translate import _
from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.modules import get_module_resource
from odoo.tools import *
import base64
import datetime

_logger = logging.getLogger(__name__)

AVAILABLE_STARS = [
    ('0', 'Low'),
    ('1', 'One Star'),
    ('2', 'Two Star'),
    ('3', 'Three Star'),
    ('4', 'Four Star'),
    ('5', 'Five Star'),
]

AVAILABLE_REV = [
    ('R', 'Room Revenue'),
    ('F', 'F&B Revenue'),
    ('M', 'Miscellaneous'),
    ('N', 'Non Revenue'),
    ('P', 'Payment'),
]

AVAILABLE_RATETYPE = [
    ('D', 'Daily'),
    ('M', 'Monthly'),
]

AVAILABLE_PAY = [
    ('CA', 'Cash'),
    ('CL', 'City Ledger'),
    ('AX', 'American Express'),
    ('DC', 'Diner Club'),
    ('MC', 'Master Card'),
    ('VS', 'Visa Card'),
    ('JC', 'JCB Card'),
    ('LC', 'Local Card'),
    ('UP', 'Union Pay Card'),
    ('OT', 'Others'),
]


class Property(models.Model):
    _name = "property.property"
    _inherit = ['mail.thread']
    _description = "Property"

    # Default Get Currency
    def default_get_currency(self):
        mmk_currency_id = self.env['res.currency'].search([('name', '=', 'MMK')
                                                           ])
        usd_currency_id = self.env['res.currency'].search([('name', '=', 'USD')
                                                           ])

        if mmk_currency_id.active is False:
            return usd_currency_id
        else:
            return mmk_currency_id

    # Default Get Country
    def default_get_country(self):
        country_id = None
        if self.currency_id:
            country_id = self.env['res.country'].search([
                ('currency_id', '=', self.currency_id.id)
            ])
        else:
            country_id = self.env['res.country'].search([('code', '=', 'MM')])
        return country_id

    is_property = fields.Boolean(string="Is Property",
                                 compute='_compute_is_property')
    hotelgroup_id = fields.Many2one('res.company',
                                    string="Parent Company",
                                    required=True)
    name = fields.Char(string='Hotel Name', required=True, index=True)
    code = fields.Char(string='Property ID', required=True)
    address1 = fields.Char(string='Address 1')
    address2 = fields.Char(string='Address 2')
    township = fields.Many2one("hms.township",
                               string='Township',
                               ondelete='restrict',
                               track_visibility=True,
                               domain="[('city_id', '=?', city_id)]")
    city_id = fields.Many2one("hms.city",
                              string='City',
                              ondelete='restrict',
                              track_visibility=True,
                              domain="[('state_id', '=?', state_id)]")
    state_id = fields.Many2one('res.country.state', string='State')
    zip = fields.Char(change_default=True)
    currency_id = fields.Many2one("res.currency",
                                  "Currency",
                                  default=default_get_currency,
                                  readonly=False,
                                  track_visibility=True,
                                  domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country',
                                 string='Country',
                                 readonly=False,
                                 requried=True,
                                 track_visibility=True,
                                 ondelete='restrict')
    phone = fields.Char(string='Phone')
    fax = fields.Char(string='Fax')
    email = fields.Char(string='Email')
    website = fields.Char(string='Website')
    sociallink = fields.Char(string='Social Link')
    roomqty = fields.Integer(string='Total Rooms',
                             compute='_compute_room_no_count')
    property_license = fields.Char(string='Property License')
    rating = fields.Selection(AVAILABLE_STARS,
                              string='Rating',
                              index=True,
                              default=AVAILABLE_STARS[0][0])
    logo = fields.Binary(string='Logo', attachment=True, store=True)
    image = fields.Binary(string='Image', attachment=True, store=True)
    contact_ids = fields.Many2many('res.partner',
                                   'property_property_contact_rel',
                                   'property_id',
                                   'partner_id',
                                   string='Contacts',
                                   track_visibility=True,
                                   domain="[('is_company', '!=', True)]")
    bankinfo_ids = fields.One2many('res.bank',
                                   'property_id',
                                   string="Bank Info")
    comments = fields.Text(string='Notes')
    roomtype_ids = fields.Many2many('room.type')
    building_ids = fields.Many2many('building.building')
    market_ids = fields.Many2many('market.segment', string="Market Segment")
    propertyroom_ids = fields.One2many('property.room',
                                       'property_id',
                                       string="Property Room")
    building_count = fields.Integer("Building",
                                    compute='_compute_building_count')
    room_count = fields.Integer("Room", compute='_compute_room_count')
    roomtype_count = fields.Integer("Room Type",
                                    compute='_compute_room_type_count')
    # roomtype_total = fields.Integer("Room Type Total",
    #                                 compute='_compute_room_type_total')
    package_ids = fields.One2many('package.package',
                                  'property_id',
                                  string="Package")
    subgroup_ids = fields.One2many('sub.group',
                                   'property_id',
                                   string="Sub Group")
    transaction_ids = fields.One2many('transaction.transaction',
                                      'property_id',
                                      string="Transaction")
    creditlimit_ids = fields.One2many('credit.limit',
                                      'property_id',
                                      string="Credit Limit")
    specialday_ids = fields.One2many('special.day',
                                     'property_id',
                                     string="Special Days")
    weekend_id = fields.One2many('weekend.weekend',
                                 'property_id',
                                 string="Weekends")
    ratecode_ids = fields.One2many('rate.code',
                                   'property_id',
                                   string="Rate Code")

    property_code_len = fields.Integer(
        "Property Code Length",
        track_visibility=True,
        default=lambda self: self.env.user.company_id.property_code_len)
    building_code_len = fields.Integer(
        "Building Code Length",
        track_visibility=True,
        default=lambda self: self.env.user.company_id.building_code_len)
    location_code_len = fields.Integer(
        "Floor Code Length",
        track_visibility=True,
        default=lambda self: self.env.user.company_id.location_code_len)

    profile_id_format = fields.Many2one(
        "pms.format",
        "Guest Profile ID Format",
        track_visibility=True,
        default=lambda self: self.env.user.company_id.profile_id_format.id)
    confirm_id_format = fields.Many2one(
        "pms.format",
        "Confirm ID Format",
        track_visibility=True,
        default=lambda self: self.env.user.company_id.confirm_id_format.id)
    cprofile_id_format = fields.Many2one(
        "pms.format",
        "Company Profile ID Format",
        track_visibility=True,
        default=lambda self: self.env.user.company_id.cprofile_id_format.id)
    gprofile_id_format = fields.Many2one(
        "pms.format",
        "Group Profile ID Format",
        track_visibility=True,
        default=lambda self: self.env.user.company_id.gprofile_id_format.id)

    _sql_constraints = [('code_unique', 'UNIQUE(code)',
                         'Hotel ID already exists! Hotel ID must be unique!')]

    @api.onchange('currency_id')
    def onchange_currency_id(self):
        for record in self:
            country_id = None
            if record.currency_id:
                country_ids = self.env['res.country'].search([
                    ('currency_id', '=', record.currency_id.id)
                ])
                if len(country_ids) > 1:
                    country_id = country_ids[0]
                else:
                    country_id = country_ids
            record.country_id = country_id

    @api.onchange('code')
    def onchange_code(self):
        for record in self:
            length = 0
            if record.code:
                length = len(record.code)
            if record.property_code_len:
                if length > record.property_code_len:
                    raise UserError(
                        _("Property code length must not exceed %s characters."
                          % (record.property_code_len)))

    def _compute_is_property(self):
        self.is_property = True

    def action_weekend(self):
        weekend = self.mapped('weekend_ids')
        action = self.env.ref('hms_ssy.weekend_action_window').read()[0]
        if (len(weekend)) == 1:
            # action['domain'] = [('id', '=', weekend.id)]
            form_view = [(self.env.ref('hms_ssy.weekend_view_form').id, 'form')
                         ]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = weekend.id
        elif len(weekend) == 0:
            form_view = [(self.env.ref('hms_ssy.weekend_view_form').id, 'form')
                         ]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = weekend.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        context = {
            'default_type': 'out_weekend',
        }
        return action

    def action_specialday(self):
        specialdays = self.mapped('specialday_ids')
        action = self.env.ref('hms_ssy.special_day_action_window').read()[0]
        if len(specialdays) >= 1:
            action['domain'] = [('id', 'in', specialdays.ids)]
        elif len(specialdays) == 0:
            form_view = [(self.env.ref('hms_ssy.special_day_view_form').id,
                          'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = specialdays.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        context = {
            'default_type': 'out_specialday',
        }
        return action

    def action_package(self):
        packages = self.mapped('package_ids')
        action = self.env.ref('hms_ssy.package_action_window').read()[0]
        if len(packages) >= 1:
            action['domain'] = [('id', 'in', packages.ids)]
        elif len(packages) == 0:
            form_view = [(self.env.ref('hms_ssy.package_view_form').id, 'form')
                         ]
            if 'views' in action['views']:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = packages.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_property_id': 'id',
        }
        return action

    def action_transaction(self):
        transactions = self.mapped('transaction_ids')
        action = self.env.ref('hms_ssy.transaction_action_window').read()[0]
        if len(transactions) >= 1:
            action['domain'] = [('id', 'in', transactions.ids)]
        elif len(transactions) == 0:
            form_view = [(self.env.ref('hms_ssy.transaction_view_form').id,
                          'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = transactions.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        context = {
            'default_type': 'out_transaction',
        }
        return action

    def action_creditlimit(self):
        credit_limit = self.mapped('creditlimit_ids')
        action = self.env.ref('hms_ssy.credit_limit_action_window').read()[0]
        if len(credit_limit) >= 1:
            action['domain'] = [('id', 'in', credit_limit.ids)]
        elif len(credit_limit) == 0:
            form_view = [(self.env.ref('hms_ssy.credit_limit_view_form').id,
                          'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = credit_limit.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        context = {
            'default_type': 'out_creditlimit',
        }
        return action

    def action_ratecode(self):
        rate_code = self.mapped('ratecode_ids')
        action = self.env.ref('hms_ssy.rate_code_action_window').read()[0]
        if len(rate_code) >= 1:
            action['domain'] = [('id', 'in', rate_code.ids)]
        elif len(rate_code) == 0:
            form_view = [(self.env.ref('hms_ssy.rate_code_view_form').id,
                          'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = rate_code.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        context = {
            'default_type': 'out_ratecode',
        }
        return action

    # Building Count
    def action_building_count(self):
        buildings = self.mapped('building_ids')
        action = self.env.ref('hms_ssy.building_action_window').read()[0]
        if len(buildings) > 1:
            action['domain'] = [('id', 'in', buildings.ids)]
        elif len(buildings) == 1:
            form_view = [(self.env.ref('hms_ssy.building_view_form').id,
                          'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = buildings.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_type': 'out_building',
        }
        return action

    def _compute_building_count(self):
        self.building_count = len(self.building_ids)

    def _compute_room_no_count(self):
        self.roomqty = len(self.propertyroom_ids)

    # Room Count
    def action_room_count(self):
        rooms = self.mapped('propertyroom_ids')
        action = self.env.ref('hms_ssy.property_room_action_window').read()[0]
        if len(rooms) > 1:
            action['domain'] = [('id', 'in', rooms.ids)]
        elif len(rooms) == 1:
            form_view = [(self.env.ref('hms_ssy.property_room_view_form').id,
                          'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = rooms.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        context = {
            'default_type': 'out_room',
        }
        return action

    def _compute_room_count(self):
        self.room_count = len(self.propertyroom_ids)

    # Room Type Count
    def action_room_type_count(self):
        room_types = self.mapped('roomtype_ids')
        action = self.env.ref('hms_ssy.room_type_action_window').read()[0]
        if len(room_types) > 1:
            action['domain'] = [('id', 'in', room_types.ids)]
        elif len(room_types) == 1:
            form_view = [(self.env.ref('hms_ssy.room_type_view_form').id,
                          'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = room_types.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        context = {
            'default_type': 'out_room_type',
        }
        return action

    def _compute_room_type_count(self):
        self.roomtype_count = len(self.roomtype_ids)

    # def _compute_room_type_total(self):
    #     self.roomtype_total = len(self.roomtype_ids)

    # @api.depends('id')
    # def _property_pc(self):
    #     for rec in self:
    #         # if(rec.id.propertyroom_ids):
    #         for roomno in rec.id.propertyroom_ids:
    #             roomno.property_id = int(roomno.property_id)

    # @api.onchange('property_id')
    # def onchange_property_id(self):
    #     roomtype_list =[]
    #     domain={}
    #     for rec in self:
    #         if(rec.property_id.roomtype_ids):
    #             for roomtype in rec.property_id.building_ids:
    #                 roomtype_list.append(roomtype.id)
    #             domain = {'roomtype_id':[('id','=', roomtype_list)]}
    #             return{'domain': domain}


# class RoomtypeCount(models.Model):
#     _name = "roomtype.count"
#     _description = "Room Type Count"

#     roomtype_ids = fields.Many2many('room.type')
#     rtype_code = fields.Char(string="Code",
#                              related='roomtype_ids.code',
#                              store=True)
#     rtype_name = fields.Char(string="Name",
#                              related='roomtype_ids.name',
#                              store=True)
#     rtype_count = fields.Integer(string="Total Room",
#                                  related='roomtype_ids.count_roomtype',
#                                  store=True)

# class Partner(models.Model):
#     _inherit = 'res.partner'

#     dob = fields.Date(string="Date of Birth")
#     image = fields.Binary(string="Image", attachment=True, store=True)
#     property_id = fields.Many2one('property.property',
#                                   string="Property",
#                                   required=True)


class Building(models.Model):
    _name = "building.building"
    _description = "Building"
    _rec_name = 'building_name'

    building_name = fields.Char(string='Building Name', required=True)
    building_type = fields.Many2one('building.type',
                                    string='Building Type',
                                    required=True)
    building_location = fields.Char(string='Location')
    building_img = fields.Binary(string='Building Image',
                                 attachment=True,
                                 store=True)
    building_desc = fields.Text(string='Description')
    building_capacity = fields.Integer(string='Capacity',
                                       default=1,
                                       required=True)
    location_ids = fields.Many2many('room.location',
                                    string="Room Location",
                                    required=True)
    _sql_constraints = [
        ('building_name_unique', 'UNIQUE(building_name)',
         'Building name already exists! Building name must be unique!')
    ]

    # location_number = fields.Integer("Location Number", compute="_room_location_count", readonly=True)

    # def get_name(self,cr, uid, ids, context=None):
    #     if context is None:
    #         context = {}
    #     if isinstance(ids, (int, long)):
    #         ids = [ids]

    #     res = []
    #     for record in self.browse(cr, uid, ids, context=context):
    #         name = record.building_name
    #         res.append(record.id, name)
    #     return res

    # @api.model
    # def name_get(self):
    #     result = []
    #     for record in self:
    #         result.append((record.id, "{}".format(record.building_name)))
    #     return result

    # @api.depends('building_capacity','location_ids')
    # def _room_location_count(self):

    #         return len(locations)

    # @api.model
    # def create(self, values):
    #     locations = values['location_ids']
    #     building_capacity = values['building_capacity']
    #     if values['location_ids'][0][2]:
    #         if len(values['location_ids'][0][2]) > building_capacity:
    #             raise UserError(
    #                 _("Location number must less than building capacity."))
    #     return super(Building, self).create(values)

    @api.constrains('location_ids')
    def check_capacity(self):
        for record in self:
            if len(record.location_ids) > record.building_capacity:
                raise UserError(
                    _("Location number must not larger than building capacity."
                      ))


class BuildingType(models.Model):
    _name = "building.type"
    _description = "Building Type"

    building_type = fields.Char(string='Building Type', required=True)
    buildingtype_desc = fields.Char(string='Description', required=True)
    _sql_constraints = [(
        'building_type_unique', 'UNIQUE(building_type)',
        'Building type already exists with this name! Building type name must be unique!'
    )]

    def name_get(self):
        result = []
        for record in self:
            result.append(
                (record.id, "{} ({})".format(record.buildingtype_desc,
                                             record.building_type)))
        return result


class RoomLocation(models.Model):
    _name = "room.location"
    _description = "Room Location"

    location_code = fields.Char(string='Code', size=3, required=True)
    location_name = fields.Char(string='Name', required=True)
    _sql_constraints = [(
        'location_code_unique', 'UNIQUE(location_code)',
        'Location code already exists with this name! Location code must be unique!'
    )]

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.location_code,
                                                       record.location_name)))
        return result


class RoomType(models.Model):
    _name = "room.type"
    _description = "Room Type"

    code = fields.Char(string='Code', size=3, required=True)
    name = fields.Char(string='Room Type', required=True)
    ratecode_id = fields.Char(string='Rate Code')
    #totalroom = fields.Integer(string='Total Rooms')
    image = fields.Binary(string='Image', attachment=True, store=True)
    roomtype_desc = fields.Text(string='Description')
    propertyroom_ids = fields.One2many('property.room',
                                       'roomtype_id',
                                       string="Property Room")

    _sql_constraints = [(
        'code_unique', 'UNIQUE(code)',
        'Room code already exists with this name! Room code name must be unique!'
    )]
    count = fields.Integer(string="Total Room", compute='_get_total')

    @api.depends('propertyroom_ids')
    def _get_total(self):
        for roomtype in self:
            roomtype.count = sum(room.total
                                 for room in roomtype.propertyroom_ids)

    # @api.depends('propertyroom_ids')
    # def count_rooms(self):
    #     for room in self:
    #         room.count = self.env['property.room'].search_count(
    #             ['roomtype_ids', '=', 'self.id'])


class RoomView(models.Model):
    _name = "room.view"
    _description = "Room View"

    name = fields.Char(string='Room View', required=True)
    roomview_desc = fields.Text(string='Description')
    _sql_constraints = [(
        'name_unique', 'UNIQUE(name)',
        'Room view already exists with this name! Room view name must be unique!'
    )]


class RoomFacility(models.Model):
    _name = "room.facility"
    _description = "Room Facility"
    _order = 'facilitytype_id'

    amenity_ids = fields.Many2many('room.amenity',
                                   string="Room Facility",
                                   required=True)
    facilitytype_id = fields.Many2one('room.facility.type',
                                      string='Facility Type',
                                      required=True)
    facility_desc = fields.Text(string="Description")


class RoomAmenity(models.Model):
    _name = "room.amenity"
    _description = "Room Amenity"

    name = fields.Char(string="Amenity Name", required=True)
    amenity_desc = fields.Text(string="Description")
    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)',
         'Room amenity name already exists! Amenity name must be unique!')
    ]


class RoomFacilityType(models.Model):
    _name = "room.facility.type"
    _description = "Room Facility Type"
    # _rec_name = 'facilitytype_desc'

    facility_type = fields.Char(string="Room Facility Type ",
                                help='Eg. EQP.....',
                                size=3,
                                required=True)
    facilitytype_desc = fields.Char(string="Description",
                                    help='Eg.Room Equipment.....',
                                    required=True)
    _sql_constraints = [(
        'facility_type_unique', 'UNIQUE(facility_type)',
        'Room facility type already exists with this name! Facility type must be unique!'
    )]

    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, "{} ({})".format(record.facilitytype_desc,
                                                    record.facility_type)))
        return res


class PropertyRoom(models.Model):
    _name = "property.room"
    _description = "Property Room"
    _group = 'roomlocation_id'
    _rec_name = 'room_no'

    # def default_roomtype_id(self):
    #     rec = self.env['property.property'].browse(
    #         self._context.get('default_property_id'))
    #     if (rec.roomtype_ids):
    #         return rec.roomtype_ids
    #     return False

    room_no = fields.Char(string="Room No", required=True)
    property_id = fields.Many2one('property.property',
                                  string="Property",
                                  required=True)
    roomtype_ids = fields.Many2many('room.type',
                                    related="property_id.roomtype_ids")
    roomtype_id = fields.Many2one('room.type',
                                  string="Room Type",
                                  domain="[('id', '=?', roomtype_ids)]",
                                  required=True)
    roomview_ids = fields.Many2many('room.view', string="Room View Code")
    building_ids = fields.Many2many('building.building',
                                    related="property_id.building_ids")
    building_id = fields.Many2one('building.building',
                                  string="Room Building",
                                  domain="[('id', '=?', building_ids)]",
                                  required=True)
    roomlocation_id = fields.Many2one('room.location',
                                      string="Location",
                                      required=True)
    facility_ids = fields.Many2many('room.facility',
                                    string="Room Facility",
                                    required=True)
    ratecode_id = fields.Char(string="Ratecode")
    room_bedqty = fields.Integer(string="Number of Beds",
                                 size=2,
                                 default=1,
                                 required=True)
    room_size = fields.Char(string="Room Size")
    room_extension = fields.Char(string="Room Extension")
    room_img = fields.Binary(string="Image", attachment=True, store=True)
    room_desc = fields.Text(string="Description")
    room_connect = fields.Char(string="Connecting Room")
    room_fostatus = fields.Char(string="FO Room Status",
                                size=2,
                                default='VC',
                                invisible=True)
    room_hkstatus = fields.Char(string="HK Room Status",
                                size=2,
                                default='VC',
                                invisible=True)
    room_status = fields.Char(string="Room Status",
                              size=2,
                              default='CL',
                              invisible=True)
    _sql_constraints = [
        ('room_no_unique', 'UNIQUE(property_id, room_no)',
         'Room number already exists! Room number must be unique!')
    ]
    total = fields.Integer(string="Total", compute='_get_total')

    def _get_total(self):
        for room in self:
            room.total = len(room.roomtype_id)

    # count_roomtype = fields.Integer(
    #     string="Total Room",
    #     compute='count_room_no',
    #     store=True,
    #     help='Contains number of room that belong to this room type')

    # @api.depends('roomtype_ids')
    # def count_room_no(self):
    #     for record in self:
    #         record.count_roomtype = len(record.propertyroom_ids.roomtype_ids)

    # def open_one2many_line(self):
    #     context = self.env.context
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Open Line',
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_model': 'property.room',
    #         'res_id': context.get('default_active_id'),
    #         'target': 'new',
    #     }

    # def _get_default_property_id(self, cr, uid, context=None):
    #     res = self.pool.get('property.property').search(cr, uid, [('property_id','=','')], context=context)
    #     return res and res[0] or False

    # Building Link with Property
    # @api.onchange('property_id')
    # def onchange_property_id(self):
    #     building_list = []
    #     domain = {}
    #     for rec in self:
    #         if (rec.property_id.building_ids):
    #             for building in rec.property_id.building_ids:
    #                 building_list.append(building.id)
    #             domain = {'building_id': [('id', '=', building_list)]}
    #             return {'domain': domain}

    # Room Type link with Property
    # @api.onchange('property_id')
    # def onchange_property_id1(self):
    #     roomtype_list = []
    #     domain = {}
    #     for rec in self:
    #         if (rec.property_id.roomtype_ids):
    #             for roomtype in rec.property_id.roomtype_ids:
    #                 roomtype_list.append(roomtype.id)
    #             domain = {'roomtype_id': [('id', '=', roomtype_list)]}
    #             return {'domain': domain}

    # Room location link with Building
    @api.onchange('building_id')
    def onchange_room_location_id(self):
        location_list = []
        domain = {}
        for rec in self:
            if (rec.building_id.location_ids):
                for location in rec.building_id.location_ids:
                    location_list.append(location.id)
                domain = {'roomlocation_id': [('id', '=', location_list)]}
                return {'domain': domain}


class MarketSegment(models.Model):
    _name = "market.segment"
    _description = "Maret Segment"
    _order = 'group_id'

    market_code = fields.Char(string="Market Code", size=3, required=True)
    market_name = fields.Char(string="Market Name", required=True)
    group_id = fields.Many2one('market.group',
                               string="Group Code",
                               required=True)
    options = fields.Selection([
        ('W', 'Walk In'),
        ('H', 'House Use'),
        ('C', 'Complimentary'),
        ('O', 'Others'),
    ],
                               string="Options")
    _sql_constraints = [(
        'market_code_unique', 'UNIQUE(market_code)',
        'Market code already exists with this name! Market code must be unique!'
    )]


class MarketGroup(models.Model):
    _name = "market.group"
    _description = "Market Group"

    group_code = fields.Char(string="Group Code", size=3, required=True)
    group_name = fields.Char(string="Group Name", required=True)
    _sql_constraints = [(
        'group_code_unique', 'UNIQUE(group_code)',
        'Market group code already exists with this name! Market group code must be unique!'
    )]

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.group_name,
                                                       record.group_code)))
        return result


class MarketSource(models.Model):
    _name = "market.source"
    _description = "Market Source"

    source_code = fields.Char(string="Source Code", size=3, required=True)
    source_desc = fields.Char(string="Description")
    _sql_constraints = [(
        'source_code_unique', 'UNIQUE(source_code)',
        'Source code already exists with this name! Source code must be unique!'
    )]


class Weekend(models.Model):
    _name = "weekend.weekend"
    _description = "Weekend"

    property_id = fields.Many2one('property.property',
                                  string="Property",
                                  required=True)
    monday = fields.Boolean(string="Monday")
    tuesday = fields.Boolean(string="Tuesday")
    wednesday = fields.Boolean(string="Wednesday")
    thursday = fields.Boolean(string="Thursday")
    friday = fields.Boolean(string="Friday")
    saturday = fields.Boolean(string="Saturday", default=True)
    sunday = fields.Boolean(string="Sunday", default=True)


class SpecialDay(models.Model):
    _name = "special.day"
    _description = "Special Day"
    _rec_name = 'special_date'

    property_id = fields.Many2one('property.property',
                                  string="Property",
                                  required=True)
    special_date = fields.Date(string="Special Date", required=True)
    special_desc = fields.Char(string="Description")


class Package(models.Model):
    _name = "package.package"
    _description = "Package"

    property_id = fields.Many2one('property.property',
                                  string="Property",
                                  required=True)
    package_code = fields.Char(string="Package Code", size=4, required=True)
    package_name = fields.Char(string="Package Name", required=True)
    _sql_constraints = [(
        'package_code_unique', 'UNIQUE(property_id, package_code)',
        'Package code already exists with this name! Package code must be unique!'
    )]


class RevenueType(models.Model):
    _name = "revenue.type"
    _description = "Revenue Type"
    _order = "rev_code"

    rev_code = fields.Char(string="Group Code", size=1, required=True)
    rev_type = fields.Selection(AVAILABLE_REV,
                                string="Revenue Type",
                                required=True)
    revtype_name = fields.Char(string="Revenue")
    rev_subgroup = fields.Boolean(string="Sub Group")
    subgroup_ids = fields.One2many('sub.group',
                                   'revtype_id',
                                   string="Sub Group")
    transaction_id = fields.Many2one('transaction.transaction',
                                     'trans_revtype')
    _sql_constraints = [
        ('rev_code_unique', 'UNIQUE(rev_code)',
         'This code already exists with this name! Group code must be unique!')
    ]

    def name_get(self):
        result = []
        for record in self:
            result.append(
                (record.id, "({} {}) {}".format(record.rev_code,
                                                record.rev_type,
                                                record.revtype_name)))
        return result

    @api.onchange('rev_type')
    def onchange_rev_code(self):
        for record in self:
            rev_type = record.rev_type
            if rev_type != False:
                record.revtype_name = dict(AVAILABLE_REV)[record.rev_type]
            if rev_type == 'P':
                record.rev_code = '9'
            elif rev_type == 'N':
                record.rev_code = '8'

    @api.constrains('rev_code', 'rev_type')
    def _check_rev_code(self):
        for record in self:
            rev_code = record.rev_code
            rev_type = record.rev_type
            if rev_code and not str(rev_code).isdigit():
                raise UserError(_("Transaction code must be digit."))
            else:
                if rev_code == '0':
                    raise UserError(
                        _("Transaction code must not start with '0'!"))
                else:
                    if rev_type == 'P':
                        if int(rev_code) != 9:
                            raise UserError(
                                _("Payment code must start with 9!"))
                    elif rev_type == 'N':
                        if int(rev_code) != 8:
                            raise UserError(
                                _("Non Revenue code must start with 8!"))
                    elif rev_type != 'P' and rev_type != 'N':
                        if int(rev_code) == 8 or int(rev_code) == 9:
                            raise UserError(_("Revenue code must be 1 ~ 7!"))


class SubGroup(models.Model):
    _name = "sub.group"
    _description = "Revenue Sub Group"

    property_id = fields.Many2one('property.property',
                                  string="Property",
                                  required=True)
    revtype_id = fields.Many2one('revenue.type',
                                 string="Revenue Type",
                                 domain="[('rev_subgroup', '=?', True)]",
                                 required=True)
    sub_group = fields.Char(string="Sub Group Code", size=1, required=True)
    sub_desc = fields.Char(string="Description", required=True)
    transsub_id = fields.Many2one('transaction.transaction', 'subgroup_id')

    _sql_constraints = [(
        'sub_group_unique', 'UNIQUE(property_id, revtype_id, sub_group)',
        'This Sub Group code already exists with this name! Sub Group Code must be unique!'
    )]

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "({}) {}".format(record.sub_group,
                                                       record.sub_desc)))
        return result

    @api.constrains('sub_group')
    def _check_sub_group(self):
        for record in self:
            sub_code = record.sub_group
            if sub_code and not str(sub_code).isdigit():
                raise UserError(_("Transaction code must be digit"))


class Transaction(models.Model):
    _name = "transaction.transaction"
    _description = "Transaction"

    property_id = fields.Many2one('property.property',
                                  string="Property",
                                  required=True,
                                  readonly=True)
    revtype_id = fields.Many2one('revenue.type',
                                 string="Revenue Type",
                                 required=True)
    revtype_name = fields.Char(String="Revenue Type")
    revsub_active = fields.Boolean(string="SubGroup")
    trans_ptype = fields.Selection(AVAILABLE_PAY, string="Pay Type")
    subgroup_ids = fields.One2many('sub.group',
                                   related="property_id.subgroup_ids")
    subgroup_id = fields.Many2one('sub.group',
                                  domain="[('id', '=?', subgroup_ids)]",
                                  string="Sub Group")
    subgroup_name = fields.Char(string="Sub Group Name", readonly=True)
    trans_code = fields.Char(string="Transaction Code",
                             size=4,
                             required=True,
                             index=True)
    trans_name = fields.Char(string="Transaction Name", required=True)
    trans_unitprice = fields.Float(string="Unit Price", required=True)
    trans_utilities = fields.Selection([
        ('Y', 'Yes'),
        ('N', 'No'),
    ],
                                       string="Utilities")
    trans_svc = fields.Boolean(string="Service Charge")
    trans_tax = fields.Boolean(string="Tax")
    trans_internal = fields.Boolean(string="Internal Use")
    trans_minus = fields.Boolean(string="Minus Nature")
    trans_type = fields.Selection([
        ('R', 'Revenue'),
        ('S', 'Service'),
        ('V', 'Tax'),
    ],
                                  string="Transaction Type")
    root_id = fields.Many2one('transaction.root',
                              compute='_compute_transaction_root',
                              store=True)
    ratecode_ids = fields.One2many('rate.code',
                                   'transcation_id',
                                   string="Rate Code")

    _sql_constraints = [(
        'trans_code_unique', 'UNIQUE(property_id, trans_code)',
        'Transaction code already exists with this name! Transaction code must be unique!'
    )]

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "({}) {}".format(record.trans_code,
                                                       record.trans_name)))
        return result

    @api.onchange('subgroup_id')
    def onchange_sub_name(self):
        for record in self:
            subgroup_id = record.subgroup_id
            record.subgroup_name = subgroup_id.sub_desc

    @api.onchange('revtype_id')
    def onchange_revtype_name(self):
        for record in self:
            subgroup_list = []
            domain = {}
            revtype_id = record.revtype_id
            record.revtype_name = revtype_id.revtype_name
            record.revsub_active = revtype_id.rev_subgroup
            if (record.revsub_active is False):
                record.subgroup_name = revtype_id.revtype_name
            else:
                if (record.revtype_id.subgroup_ids):
                    for subgroup in record.revtype_id.subgroup_ids:
                        if (subgroup.property_id == record.property_id):
                            subgroup_list.append(subgroup.id)
                    domain = {'subgroup_id': [('id', 'in', subgroup_list)]}
                return {'domain': domain}

    @api.constrains('trans_code', 'revtype_id')
    def _check_trans_code(self):
        for record in self:
            trans_revtype = record.revtype_id.rev_type
            trans_code = record.trans_code
            rev_code = record.revtype_id.rev_code
            sub_code = record.subgroup_id.sub_group
            if trans_revtype == 'P':
                if trans_code and not str(trans_code).isdigit():
                    raise UserError(_("Transaction code must be digit!"))
                else:
                    if int(record.trans_code) < 9000:
                        raise UserError(
                            _("Payment Code must be greather than 9000!"))
            elif trans_revtype != 'P':
                if trans_code and not str(trans_code).isdigit():
                    raise UserError(_("Transaction code must be digit!"))
                else:
                    if int(record.trans_code) > 9000:
                        raise UserError(
                            _("Revenue code must be less than 9000!"))
                    else:
                        if int(record.trans_code) < 1000:
                            raise UserError(
                                _("Revenue code must be 4 digits!"))
                        else:
                            if record.trans_code[0:1] != rev_code:
                                raise UserError(
                                    _("Transaction code must start with Revenue Code!"
                                      ))
                            else:
                                if sub_code != False:
                                    if record.trans_code[1:2] != sub_code:
                                        raise UserError(
                                            _("Transaction code must start with Revenue Code + Sub Group Code. Eg. F&B Revenu (2) and BF Revenue (0)-> Transaction code must start with '20'!"
                                              ))

    @api.depends('trans_code')
    def _compute_transaction_root(self):
        # this computes the first 2 digits of the transaction.
        # This field should have been a char, but the aim is to use it in a side panel view with hierarchy, and it's only supported by many2one fields so far.
        # So instead, we make it a many2one to a psql view with what we need as records.
        for record in self:
            record.root_id = record.trans_code and (
                ord(record.trans_code[0]) * 1000 +
                ord(record.trans_code[1])) or False


class TransactionRoot(models.Model):
    _name = 'transaction.root'
    _description = 'Transaction codes first 2 digits'
    _auto = False

    name = fields.Char()
    revname = fields.Char()
    parent_id = fields.Many2one('transaction.root', string="Superior Level")
    group = fields.Many2one('sub.group')

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "({}) {}".format(record.revname,
                                                       record.name)))
        return result

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (
            SELECT DISTINCT ASCII(trans_code) * 1000 + ASCII(SUBSTRING(trans_code,2,1)) AS id,
                   LEFT(trans_code,2) AS name,
                   subgroup_name as revname,
                   ASCII(trans_code) AS parent_id,
                   subgroup_id as group
            FROM transaction_transaction WHERE trans_code IS NOT NULL
            UNION ALL
            SELECT DISTINCT ASCII(trans_code) AS id,
                   LEFT(trans_code,1) AS name,
                   revtype_name as revname,
                   NULL::int AS parent_id,
                   subgroup_id as group
            FROM transaction_transaction WHERE trans_code IS NOT NULL
            )''' % (self._table, ))


class RsvnType(models.Model):
    _name = "rsvn.type"
    _description = "Reservation Type"

    rsvn_name = fields.Char(string="Reservation Type", size=30, required=True)
    rsvn_options = fields.Selection([
        ('CF', 'Confirmed'),
        ('UC', 'Unconfirmed'),
    ],
                                    string="Options",
                                    required=True)
    _sql_constraints = [(
        'rsvn_name_unique', 'UNIQUE(rsvn_name)',
        'Reservation type already exists with this name! Reservation type must be unique!'
    )]


class RsvnStatus(models.Model):
    _name = "rsvn.status"
    _description = "Reservation Status"

    rsvn_code = fields.Char(string="Reservation Status", size=3, required=True)
    rsvn_status = fields.Char(string="Description", required=True)
    _sql_constraints = [(
        'rsvn_code_unique', 'UNIQUE(rsvn_code)',
        'Reservation status already exists with this name! Reservation status must be unique!'
    )]


class CreditLimit(models.Model):
    _name = "credit.limit"
    _description = "Credit Limit"
    _group = "payment_type"

    property_id = fields.Many2one('property.property',
                                  string="Property",
                                  required=True,
                                  readonly=True)
    payment_type = fields.Selection(AVAILABLE_PAY,
                                    string="Payment Type",
                                    required=True)
    crd_startdate = fields.Date(string="Start Date", required=True)
    crd_enddate = fields.Date(string="End Date",
                              required=True)  #compute="get_end_date",
    crd_limit = fields.Float(string="Credit Limit")

    @api.onchange('crd_startdate', 'crd_enddate')
    @api.constrains('crd_startdate', 'crd_enddate')
    def get_two_date_comp(self):
        start_date = self.crd_startdate
        end_date = self.crd_enddate
        if start_date and end_date and start_date > end_date:
            raise ValidationError("End Date cannot be set before Start Date.")

    @api.onchange('payment_type', 'crd_enddate')
    def get_end_date(self):
        same_payment_objs = self.env['credit.limit'].search[(
            'payment_type', '=', self.payment_type)]
        tmp_end_date = datetime.date(1000, 1, 11)
        same_payment = self.env[
            'credit.limit']  # This is Null Object assignment
        for record in same_payment_objs:
            if record.crd_enddate > tmp_end_date:
                tmp_end_date = record.crd_enddate
                same_payment = record
            if same_payment:
                self.crd_startdate = same_payment.crd_enddate + timedelta(
                    days=1)


class RateCode(models.Model):
    _name = "rate.code"
    _description = "Rate Code"
    _rec_name = "ratecode_name"

    is_ratecode = fields.Boolean(string='Is ratecode',
                                 compute='_compute_is_ratecode')
    property_id = fields.Many2one('property.property',
                                  string="Property",
                                  required=True,
                                  readonly=True)
    rate_code = fields.Char(string="Rate Code", size=10, required=True)
    ratecode_name = fields.Char(string="Description", required=True)
    roomtype_ids = fields.Many2many("room.type",
                                    related="property_id.roomtype_ids")
    roomtype_id = fields.Many2one('room.type',
                                  string="Room Type",
                                  domain="[('id', '=?', roomtype_ids)]",
                                  required=True)
    transaction_ids = fields.One2many('transaction.transaction',
                                      related="property_id.transaction_ids")
    transcation_id = fields.Many2one('transaction.transaction',
                                     domain="[('id', '=?', transaction_ids)]",
                                     string="Transcation",
                                     required=True)
    ratecode_type = fields.Selection(AVAILABLE_RATETYPE,
                                     string="Type",
                                     default='D',
                                     required=True)
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    normal_price1 = fields.Float(string="Normal Price 1")
    normal_price2 = fields.Float(string="Normal Price 2")
    normal_price3 = fields.Float(string="Normal Price 3")
    normal_price4 = fields.Float(string="Normal Price 4")
    weekend_price1 = fields.Float(string="Weekend Price 1")
    weekend_price2 = fields.Float(string="Weekend Price 2")
    weekend_price3 = fields.Float(string="Weekend Price 3")
    weekend_price4 = fields.Float(string="Weekend Price 4")
    special_price1 = fields.Float(string="Special Price 1")
    special_price2 = fields.Float(string="Special Price 2")
    special_price3 = fields.Float(string="Special Price 3")
    special_price4 = fields.Float(string="Special Price 4")
    discount_percent = fields.Float(string="Discount Percentage", default=10.0)
    discount_amount = fields.Float(string="Discount Amount", default=50.0)

    def _compute_is_ratecode(self):
        self.is_ratecode = True

    @api.onchange('rate_code', 'end_date')
    def get_end_date(self):
        same_ratecode_objs = self.env['rate.code'].search([('rate_code', '=',
                                                            self.rate_code)])
        tmp_end_date = datetime.date(1000, 1, 11)
        same_ratecode = self.env['rate.code']  # This is Null Object assignment
        for rec in same_ratecode_objs:
            if rec.end_date > tmp_end_date:
                tmp_end_date = rec.end_date
                same_ratecode = rec
            if same_ratecode:
                self.start_date = same_ratecode.end_date + timedelta(days=1)

    def action_change_new_rate(self):
        action = self.env.ref('hms_ssy.rate_code_action_window').read()[0]

        return {
            'name':
            _('Change New Rate'),
            'view_type':
            'form',
            'view_mode':
            'form',
            'view_id':
            self.env.ref('hms_ssy.rate_code_view_form').id,
            'res_model':
            'rate.code',
            'context':
            "{'type':'out_ratecode','default_rate_code':'" + self.rate_code +
            "','default_ratecode_name':'" + self.ratecode_name +
            "','default_ratecode_type':'" + self.ratecode_type + "'}",
            'type':
            'ir.actions.act_window',
            'target':
            'new',
        }
