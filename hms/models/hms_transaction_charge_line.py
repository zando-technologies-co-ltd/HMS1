import base64
import logging

from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.modules import get_module_resource
from odoo.tools import *
from datetime import datetime, date, timedelta


class HMSTransactionChargeLine(models.Model):
    _name = 'hms.room.transaction.charge.line'
    _description = "Room Charges Type"
    _order = 'transaction_date'
    _inherit = ['mail.thread']

    def get_reservation_line_id(self):
        reservation_line = self.env['hms.reservation.line'].browse(
            self._context.get('reservation_line_id', []))
        if reservation_line:
            return reservation_line

    property_id = fields.Many2one('property.property', string="Property")
    transaction_id = fields.Many2one(
        'transaction.transaction',
        string='Transaction',
        domain="[('property_id', '=?', property_id)]")
    reservation_line_id = fields.Many2one("hms.reservation.line",
                                          "Reservation",
                                          default=get_reservation_line_id)
    rate = fields.Float("Rate", store=True)
    total_amount = fields.Float("Total")
    active = fields.Boolean(default=True)
    package_ids = fields.Many2many(
        'package.header', related="reservation_line_id.package_id.package_ids")
    package_id = fields.Many2one('package.header', string='Package')
    total_room = fields.Integer('Rooms', related="reservation_line_id.rooms")
    transaction_date = fields.Date("Date")
    ref = fields.Char(string="Reference")

    @api.onchange('package_id')
    def onchange_rate(self):
        for rec in self:
            package_id = rec.package_id
            reservation_line_id = rec.reservation_line_id
            rec.rate = reservation_line_id.rate_calculate(
                package_id, reservation_line_id)
            rec.total_amount = reservation_line_id.total_amount_calculate(
                rec.rate, package_id, reservation_line_id)

            # rec.transaction_id = rec.package_id.transaction_id
            # if rec.package_id.rate_attribute == 'INR':
            #     if rec.package_id.Calculation_method == 'FIX':
            #         if rec.package_id.reservation_fields_id:
            #             if rec.package_id.reservation_fields_id.code == 'BF':
            #                 rec.rate = rec.reservation_line_id.ratecode_id.adult_bf
            #             elif rec.package_id.reservation_fields_id.code == 'EB':
            #                 rec.rate = rec.reservation_line_id.ratecode_id.extra_bed
            #             elif rec.package_id.reservation_fields_id.code == 'CBF':
            #                 rec.rate = rec.reservation_line_id.ratecode_id.child_bf
            #         else:
            #             rec.rate = rec.total_amount = rec.package_id.Fix_price
            #     elif rec.package_id.Calculation_method == 'PA':
            #         if rec.package_id.reservation_fields_id:
            #             if rec.package_id.reservation_fields_id.code == 'BF':
            #                 rec.rate = rec.reservation_line_id.ratecode_id.adult_bf
            #                 rec.total_amount = rec.reservation_line_id.ratecode_id.adult_bf * rec.reservation_line_id.pax
            #             elif rec.package_id.reservation_fields_id.code == 'EB':
            #                 rec.rate = rec.reservation_line_id.ratecode_id.extra_bed
            #                 rec.total_amount = rec.reservation_line_id.ratecode_id.extra_bed * rec.reservation_line_id.pax
            #             elif rec.package_id.reservation_fields_id.code == 'CBF':
            #                 rec.rate = rec.reservation_line_id.ratecode_id.child_bf
            #                 rec.total_amount = rec.rate * rec.reservation_line_id.pax
            #         else:
            #             rec.rate = rec.package_id.Fix_price
            #             rec.total_amount = rec.rate * rec.reservation_line_id.pax
            #     elif rec.package_id.Calculation_method == 'PC':
            #         if rec.package_id.reservation_fields_id:
            #             if rec.package_id.reservation_fields_id.code == 'BF':
            #                 rec.rate = rec.reservation_line_id.ratecode_id.adult_bf
            #                 rec.total_amount = rec.rate * rec.reservation_line_id.child
            #             elif rec.package_id.reservation_fields_id.code == 'EB':
            #                 rec.rate = rec.reservation_line_id.ratecode_id.extra_bed
            #                 rec.total_amount = rec.rate * rec.reservation_line_id.child
            #             elif rec.package_id.reservation_fields_id.code == 'CBF':
            #                 rec.rate = rec.reservation_line_id.ratecode_id.child_bf
            #                 rec.total_amount = rec.rate * rec.reservation_line_id.child
            #         else:
            #             rec.rate = rec.package_id.Fix_price
            #             rec.total_amount = rec.rate * rec.reservation_line_id.child
            #     elif rec.package_id.Calculation_method == 'CBP':
            #         if rec.package_id.reservation_fields_id:
            #             if rec.package_id.reservation_fields_id.code == 'BF':
            #                 rec.rate = rec.reservation_line_id.ratecode_id.adult_bf
            #                 rec.total_amount = rec.rate * rec.reservation_line_id.child_bfpax
            #             elif rec.package_id.reservation_fields_id.code == 'EB':
            #                 rec.rate = rec.reservation_line_id.ratecode_id.extra_bed
            #                 rec.total_amount = rec.rate * rec.reservation_line_id.child_bfpax
            #             elif rec.package_id.reservation_fields_id.code == 'CBF':
            #                 rec.rate = rec.reservation_line_id.ratecode_id.child_bf
            #                 rec.total_amount = rec.rate * rec.reservation_line_id.child_bfpax
            #         else:
            #             rec.rate = rec.package_id.Fix_price
            #             rec.total_amount = rec.rate * rec.reservation_line_id.child_bfpax
            #     elif rec.package_id.Calculation_method == 'NEB':
            #         if rec.package_id.reservation_fields_id:
            #             if rec.package_id.reservation_fields_id.code == 'BF':
            #                 rec.rate = rec.reservation_line_id.ratecode_id.adult_bf
            #                 rec.total_amount = rec.rate * rec.reservation_line_id.extrabed
            #             elif rec.package_id.reservation_fields_id.code == 'EB':
            #                 rec.rate = rec.reservation_line_id.ratecode_id.extra_bed
            #                 rec.total_amount = rec.rate * rec.reservation_line_id.extrabed
            #             elif rec.package_id.reservation_fields_id.code == 'CBF':
            #                 rec.rate = rec.reservation_line_id.ratecode_id.child_bf
            #                 rec.total_amount = rec.rate * rec.reservation_line_id.extrabed
            #         else:
            #             rec.rate = rec.package_id.Fix_price
            #             rec.total_amount = rec.rate * rec.reservation_line_id.extrabed
