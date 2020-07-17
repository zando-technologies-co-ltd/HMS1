# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ReportHMSReservationLineStatus(models.Model):
    _name = "report.hms.reservation.line.status"
    _description = "Reservation By State"
    _auto = False

    property_id = fields.Many2one('property.property')
    # confirm_no = fields.Char('Reservation No', size=64, readonly=True)
    nbr = fields.Integer('Reservation', readonly=True)
    state = fields.Selection([('booking', 'Booking'), ('reservation', 'Reservation'),
                              ('confirm', 'Confirm'),
                              ('cancel', 'Cancel'),('checkin','CheckIn')], 'Status', size=16,
                             readonly=True)

    def init(self):
        """
        This method is for initialization for report hotel reservation
        status Module.
        @param self: The object pointer
        @param cr: database cursor
        """
        self.env.cr.execute("""
            create or replace view report_hms_reservation_line_status as (
                select
                    min(id) as id,
                    property_id,
                    state,
                    count(*) as nbr
                from
                    hms_reservation_line 
                group by state,property_id
            )""")
