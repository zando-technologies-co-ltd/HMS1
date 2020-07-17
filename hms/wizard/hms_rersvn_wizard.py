import datetime
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class HMSRersvnWizard(models.TransientModel):
    _name = "hms.rersvn_wizard"
    _description = "Re Reservation Wizard"

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
                                       required=True,
                                       default=1)
    reservation_status = fields.Many2one('rsvn.status',
                                         "Reservation Status",
                                         required=True)

    def action_rersvn_wiz(self):
        reservations = self.env['hms.reservation'].browse(
            self._context.get('active_id', []))

        state = ''
        if (self.reservation_type.rsvn_name == 'Confirmed'):
            state = 'confirm'
        else:
            state = 'reservation'
        for d in reservations.reservation_line_ids:
            if d.state == 'cancel':
                #Update Availability
                property_id = d.property_id.id
                arrival = d.arrival
                departure = d.departure
                room_type = d.room_type.id
                rooms = d.rooms
                reduce = False
                status =' '
                d._state_update_forecast(state,property_id,arrival,departure,room_type,rooms,reduce,status)
                d.write({
                    'reservation_type': self.reservation_type,
                    'reservation_status': self.reservation_status,
                    'state': state,
                    'is_cancel': False,
                })
        reservations.write({
            'reservation_type': self.reservation_type,
            'reservation_status': self.reservation_status,
            'state': state,
            'is_full_cancel': False,
        })
        hfo_reservation = self.env['hms.reservation.line'].search([('reservation_id', '=', reservations.id),('room_type', '=ilike', 'H%')])
        if hfo_reservation:
            hfo_reservation.write({'state': state})
        # reservations.confirm_status()
        # return reservations.send_mail()


class HMSRersvnLineWizard(models.TransientModel):
    _name = "hms.rersvn_line_wizard"
    _description = "Re Reservation Wizard"

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
                                       required=True,
                                       default=1)
    reservation_status = fields.Many2one('rsvn.status',
                                         "Reservation Status",
                                         required=True)

    def action_rersvn_line_wiz(self):
        reservation_lines = self.env['hms.reservation.line'].browse(
            self._context.get('active_id'))
        state = ''
        if (self.reservation_type.rsvn_name == 'Confirmed'):
            state = 'confirm'
        else:
            state = 'reservation'

        for d in reservation_lines:
            if d.state == 'cancel':
                property_id = d.property_id.id
                arrival = d.arrival
                departure = d.departure
                room_type = d.room_type.id
                rooms = d.rooms
                reduce = False
                status =' '
                d._state_update_forecast(state,property_id,arrival,departure,room_type,rooms,reduce,status)
                d.write({
                    'reservation_type': self.reservation_type,
                    'reservation_status': self.reservation_status,
                    'state': state,
                    'is_cancel': False,
                })
        # 1st time changes cancel to confirm or reservation
        if (reservation_lines.reservation_id.state == 'cancel'):
            reservation_lines.reservation_id.write({
                'state':
                state,
                'reservation_type':
                reservation_lines.reservation_type,
                'reservation_status':
                reservation_lines.reservation_status,
                'is_full_cancel':
                False,
            })
            hfo_reservation = self.env['hms.reservation.line'].search([('reservation_id', '=', reservation_lines.reservation_id.id),('room_type', '=ilike', 'H%')]) 
            if hfo_reservation:
                hfo_reservation.write({'state': state})
        else:
            confirm = 0
            for d in reservation_lines.reservation_id.reservation_line_ids:

                if d.state == 'confirm':
                    if d.room_type.code[0] != 'H':
                        confirm = confirm + 1

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
            else:
                reservation_lines.reservation_id.write({
                    'state':
                    'confirm',
                    'reservation_type':
                    reservation_lines.reservation_type,
                    'reservation_status':
                    reservation_lines.reservation_status,
                })
                hfo_reservation = self.env['hms.reservation.line'].search([('reservation_id', '=', reservation_lines.reservation_id.id),('room_type', '=ilike', 'H%')])
                if hfo_reservation:
                    hfo_reservation.write({'state': 'confirm'})

            # All Reservation line State are same, update reservation state
        rec = 0
        for d in reservation_lines.reservation_id.reservation_line_ids:

            if d.state != reservation_lines.state:
                rec = rec + 1
        if rec == 0:
            reservation_lines.reservation_id.write({
                'state':
                state,
                'reservation_type':
                reservation_lines.reservation_type,
                'reservation_status':
                reservation_lines.reservation_status,
            })
            hfo_reservation = self.env['hms.reservation.line'].search([('reservation_id', '=', reservation_lines.reservation_id.id),('room_type', '=ilike', 'H%')])
            if hfo_reservation:
                hfo_reservation.write({'state': state})
        # return reservations.send_mail()