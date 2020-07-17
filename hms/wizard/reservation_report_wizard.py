from odoo import models, fields, api
from odoo.exceptions import UserError


class ReservationReportWizard(models.TransientModel):
    _name = 'hms.reservation_report_wizard'

    property_id = fields.Many2one('property.property',
                                  string="Property",
                                  required=True)
    date_start = fields.Date(string='Start Date',
                             required=True,
                             default=fields.Date.today)
    date_end = fields.Date(string='End Date',
                           required=True,
                           default=fields.Date.today)

    # def print_report(self):
    #     data = {
    #         'ids': self.ids,
    #         'model': self._name,
    #         'form': {
    #             'date_start': self.date_start,
    #             'date_end': self.date_end,
    #             'property_id': self.property_id.id,
    #         },
    #     }
    #     return self.env.ref('hms.reservation_report').report_action([],
    #                                                                 data=data)

    # def print_report(self):
    #     datas = {'ids': self.env.context.get('active_ids', [])}
    #     res = self.read(['property_id', 'date_start', 'date_end'])
    #     res = res and res[0] or {}
    #     datas['form'] = res
    #     return self.env.ref('hms.reservation_report').report_action([],
    #                                                                 data=datas)

    def get_report(self):
        data = {
            'ids': self.ids,
            'model': 'hms.reservation.line',
            'form': self.read(['property_id', 'date_start', 'date_end'])[0]
        }

        # ref `module_name.report_id` as reference.
        return self.env.ref('hms.reservation_report').report_action(self,
                                                                    data=data)


class ExpectedArrReportWizard(models.TransientModel):
    _name = 'hms.expected_arr_report_wizard'

    property_id = fields.Many2one('property.property',
                                  string="Property",
                                  required=True)
    arr_date = fields.Date(string='Arrival Date',
                           required=True,
                           default=fields.Date.today)
    type_ = fields.Selection(
        string='Type',
        selection=[('individual', 'Individual'), ('group', 'Group')],
    )

    def get_report(self):
        data = {
            'ids': self.ids,
            'model': 'hms.reservation.line',
            'form': self.read(['property_id', 'arr_date', 'type_'])[0]
        }

        # ref `module_name.report_id` as reference.
        return self.env.ref('hms.expected_arrival_report').report_action(
            self, data=data)

    # @api.depends('is_group')
    # def _compute_type(self):
    #     for partner in self:
    #         if partner.is_group or self._context.get(
    #                 'default_type') == 'group':
    #             partner.type = 'group'
    #             partner.is_group = True
    #         else:
    #             partner.type = 'individual'

    # def _write_type(self):
    #     for partner in self:
    #         partner.is_group = partner.type == 'group'

    # @api.onchange('type')
    # def onchange_type(self):
    #     self.is_group = (self.type == 'group')
