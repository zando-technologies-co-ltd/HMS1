import datetime
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class HMSRsvnUnconfirmWizard(models.TransientModel):
    _name = "hms.rsvn_unconfirm_wizard"
    _description = "Unconfirm Wizard"

    def get_reservation_id(self):
        reservation = self.env['hms.reservation'].browse(
            self._context.get('active_id', []))
        if reservation:
            return reservation

    reservation_id = fields.Many2one("hms.reservation",
                                     default=get_reservation_id,
                                     store=True)
    reservation_no = fields.Char("Reservation",
                                 related="reservation_id.confirm_no",
                                 store=True)
    reservation_type = fields.Many2one('rsvn.type',
                                       "Reservation Type",
                                       readonly=True,
                                       default=2)
    reservation_status = fields.Many2one('rsvn.status', "Reservation Status")

    def action_unconfirm_wiz(self):
        reservations = self.env['hms.reservation'].browse(
            self._context.get('active_id', []))
        
        # hfo_reservation = self.env['hms.reservation.line'].search([('reservation_id', '=',reservations.id),('room_type.code', '=', 'HFO')])
        # no_hfo_reservation = list(set(reservations.reservation_line_ids)- set(hfo_reservation))

        for d in reservations.reservation_line_ids:
            if d.state == 'confirm':
                #Update Availability
                state = d.state
                property_id = d.property_id.id
                arrival = d.arrival
                departure = d.departure
                room_type = d.room_type.id
                rooms = d.rooms
                reduce = True
                status ='reservation'
                d._state_update_forecast(state,property_id,arrival,departure,room_type,rooms,reduce,status)
                d.write({
                    'reservation_type': self.reservation_type,
                    'reservation_status': self.reservation_status,
                    'state': status,
                })
        reservations.write({
            'reservation_type': self.reservation_type,
            'reservation_status': self.reservation_status,
            'state': 'reservation',
        })
        hfo_reservation = self.env['hms.reservation.line'].search([('reservation_id', '=', reservations.id),('room_type', '=ilike', 'H%')])
        if hfo_reservation:
            hfo_reservation.write({'state': 'reservation'})
        # return reservations.send_mail()


class HMSRsvnUnconfirmLineWizard(models.TransientModel):
    _name = "hms.rsvn_unconfirm_line_wizard"
    _description = "Unconfirm Wizard"

    def get_reservation_line_id(self):
        reservation_line = self.env['hms.reservation.line'].browse(
            self._context.get('active_id', []))
        if reservation_line:
            return reservation_line

    reservation_line_id = fields.Many2one("hms.reservation.line",
                                          default=get_reservation_line_id,
                                          store=True)
    reservation_no = fields.Char("Reservation",
                                 related="reservation_line_id.confirm_no",
                                 store=True)
    reservation_type = fields.Many2one('rsvn.type',
                                       "Reservation Type",
                                       readonly=True,
                                       default=2)
    reservation_status = fields.Many2one('rsvn.status', "Reservation Status")

    def action_unconfirm_line_wiz(self):
        reservation_lines = self.env['hms.reservation.line'].browse(
            self._context.get('active_id'))
        for d in reservation_lines:
            #Update Availability
            if d.state == 'confirm':
                state = d.state
                property_id = d.property_id.id
                arrival = d.arrival
                departure = d.departure
                room_type = d.room_type.id
                rooms = d.rooms
                reduce = True
                status ='reservation'
                d._state_update_forecast(state,property_id,arrival,departure,room_type,rooms,reduce,status)
                d.write({
                    'reservation_type': self.reservation_type,
                    'reservation_status': self.reservation_status,
                    'state': status,
                })
        rec = 0
        confirm = 0
        for d in reservation_lines.reservation_id.reservation_line_ids:

            if d.state != reservation_lines.state:
                rec = rec + 1
            if d.state == 'confirm':
                if d.room_type.code[0] != 'H':
                    confirm = confirm + 1
        if rec == 0:
            reservation_lines.reservation_id.write({
                'state':
                'reservation',
                'reservation_type':
                reservation_lines.reservation_type,
                'reservation_status':
                reservation_lines.reservation_status,
            })
            hfo_reservation = self.env['hms.reservation.line'].search([('reservation_id', '=', reservation_lines.reservation_id.id),('room_type', '=ilike', 'H%')]) 
            if hfo_reservation:
                hfo_reservation.write({'state': 'reservation'})
        else:
            if confirm == 0:
                reservation_lines.reservation_id.write({
                    'state':
                    'reservation',
                    'reservation_type':
                    reservation_lines.reservation_type,
                    'reservation_status':
                    reservation_lines.reservation_status,
                })
                hfo_reservation = self.env['hms.reservation.line'].search([('reservation_id', '=', reservation_lines.reservation_id.id),('room_type', '=ilike', 'H%')]) 
                if hfo_reservation:
                    hfo_reservation.write({'state': 'reservation'})
        # return reservations.send_mail()
