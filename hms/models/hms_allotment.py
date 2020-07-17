from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.modules import get_module_resource
#from odoo.tools import image_colorize, image_resize_image_big
from odoo.tools import *
import base64
import datetime


class HMSAllotment(models.Model):
    _name = "hms.allotment"
    _inherit = ['mail.thread']
    _description = "Allotment"
    _order = "name"

    name=fields.Char("Allotment Name", required=True)
    description = fields.Char("Description", required=True)
    property_id = fields.Many2one('property.property', track_visibility=True)
    cut_off = fields.Boolean(default=True, track_visibility=True)
    active = fields.Boolean(default=True, track_visibility=True)
    allotment_line_ids = fields.One2many('hms.allotment.line','allotment_id','Allotment')
    state = fields.Selection([('initial', 'Initial'), ('open', "Open"),('close', "Close")],
                        string='Status',
                        readonly=True,
                        copy=False,
                        store=True,
                        default='initial',
                        track_visibility=True)

class HMSAllotmentLine(models.Model):
    _name = 'hms.allotment.line'
    _inherit = ['mail.thread']
    _description = "Allotment Line"

    allotment_id = fields.Many2one("hms.allotment",
                                "Allotment Details",
                                track_visibility=True)
    property_id = fields.Many2one("property.property",             
                                store=True,
                                track_visibility=True)
    roomtype_ids = fields.Many2many("room.type", related="property_id.roomtype_ids")
    roomtype_id = fields.Many2one('room.type', string="Room Type", domain="[('id', '=?', roomtype_ids)]", required=True)
    ratecode_id = fields.Many2one('rate.code', string="Rate Code")
    start_date = fields.Date(string="Start Date",
                             readonly=False,
                             required=True,
                             store=True,
                             track_visibility=True)
    end_date = fields.Date(string="End Date",
                           readonly=False,
                           required=True,
                           store=True,
                           track_visibility=True)
    cut_off_days = fields.Integer(string="Cut off Days")
    monday = fields.Integer(string="Mon")
    tuesday = fields.Integer(string="Tue")
    wednesday = fields.Integer(string="Wed")
    thursday = fields.Integer(string="Thu")
    friday = fields.Integer(string="Fri")
    saturday = fields.Integer(string="Sat")
    sunday = fields.Integer(string="Sun")
    state = fields.Selection([('initial', 'Initial'), ('open', "Open"),('close', "Close")],
                            related="allotment_id.state",
                            string='Status',
                            readonly=True,
                            copy=False,
                            store=True,
                             default=lambda *a: 'initial',
                            track_visibility=True)
    

    
    

