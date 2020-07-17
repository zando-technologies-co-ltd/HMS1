import datetime
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class HMSRsvnConfirmWizard(models.TransientModel):
    _name = "hms.rsvn_confirm_wizard"
    _description = "Confirm Wizard"

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
                                       default=1)
    reservation_status = fields.Many2one('rsvn.status', "Reservation Status")

    def action_confirm_wiz(self):
        reservations = self.env['hms.reservation'].browse(
            self._context.get('active_id', []))
        
        # hfo_reservation = self.env['hms.reservation.line'].search([('reservation_id', '=',reservations.id),('room_type.code', '=', 'HFO')])
        # no_hfo_reservation = list(set(reservations.reservation_line_ids)- set(hfo_reservation))
        
        for d in reservations.reservation_line_ids:
            if d.state == 'reservation':
                #Update Availability
                state = d.state
                property_id = d.property_id.id
                arrival = d.arrival
                departure = d.departure
                room_type = d.room_type.id
                rooms = d.rooms
                reduce = True
                status ='confirm'
                d._state_update_forecast(state,property_id,arrival,departure,room_type,rooms,reduce,status)
                d.write({
                    'reservation_type': self.reservation_type,
                    'reservation_status': self.reservation_status,
                    'state': status,
                })
            
                
        # Update Reservation
        reservations.write({
            'reservation_type': self.reservation_type,
            'reservation_status': self.reservation_status,
            'state': 'confirm',
        })
        hfo_reservation = self.env['hms.reservation.line'].search([('reservation_id', '=', reservations.id),('room_type', '=ilike', 'H%')])
        if hfo_reservation:
            hfo_reservation.write({'state': 'confirm'})
        # reservations.confirm_status()
        # return reservations.send_mail()


class HMSRsvnConfirmLineWizard(models.TransientModel):
    _name = "hms.rsvn_confirm_line_wizard"
    _description = "Confirm Wizard"

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
                                       default=1)
    reservation_status = fields.Many2one('rsvn.status', "Reservation Status")

    def action_confirm_line_wiz(self):
        reservation_lines = self.env['hms.reservation.line'].browse(
            self._context.get('active_id'))
        for d in reservation_lines:
            #Update Availability
            if d.state == 'reservation':
                state = d.state
                property_id = d.property_id.id
                arrival = d.arrival
                departure = d.departure
                room_type = d.room_type.id
                rooms = d.rooms
                reduce = True
                status ='confirm'
                d._state_update_forecast(state,property_id,arrival,departure,room_type,rooms,reduce,status)
                d.write({
                    'reservation_type': self.reservation_type,
                    'reservation_status': self.reservation_status,
                    'state': status,
                })
        # Check and update confirm state to main reservation
        rec = 0
        for d in reservation_lines.reservation_id.reservation_line_ids:
            if d.state == 'confirm':
                if d.room_type.code[0] != 'H':
                    rec = rec + 1

        if rec > 0:
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

