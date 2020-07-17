import time
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from dateutil.relativedelta import relativedelta
from dateutil import parser
from odoo import api, fields, models


class ReservationReport(models.AbstractModel):
    """
        Abstract Model specially for report template.
        _name = Use prefix `report.` along with `module_name.report_name`
    """
    _name = 'report.hms.report_reservation_qweb'
    _description = 'Reservation Report'

    def get_reservation_list(self, property_id, date_start, date_end):
        reservation_line_obj = self.env['hms.reservation.line'].search([
            ('property_id', '=', property_id[0]),
            ('arrival', '>=', date_start), ('departure', '<=', date_end)
        ])
        return reservation_line_obj

    @api.model
    def _get_report_values(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        if data is None:
            data = {}
        if not docids:
            docids = data.get('ids', data.get('active_ids'))

        property_id = data['form']['property_id']
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        folio_profile = self.env['hms.reservation.line'].search([
            ('property_id', '=', property_id[0]),
            ('arrival', '>=', date_start), ('departure', '<=', date_end)
        ])
        # date_start = data.get('date_start', fields.Date.today())
        # date_end = data['form'].get(
        #     'date_end',
        #     str(datetime.now() +
        #         relativedelta(months=+1, day=1, days=-1))[:10])

        rm_act = self.with_context(data['form'].get('used_context', {}))
        get_reservation_list = rm_act.get_reservation_list(
            property_id, date_start, date_end)

        # Change Date Format to D/M/Y after all processes are done
        date_start = datetime.strptime(date_start,
                                       '%Y-%m-%d').strftime('%d/%m/%Y')
        date_end = datetime.strptime(date_end, '%Y-%m-%d').strftime('%d/%m/%Y')
        return {
            'doc_ids': docids,
            'doc_model': 'hms.reservation.line',
            # 'data': data['form'],
            'date_start': date_start,
            'date_end': date_end,
            'property_id': property_id[1],
            'docs': folio_profile,
            'time': time,
            'get_reservation_list': get_reservation_list,
        }


class ExpectedArrivalReport(models.AbstractModel):
    """
        Abstract Model specially for report template.
        _name = Use prefix `report.` along with `module_name.report_name`
    """
    _name = 'report.hms.report_expected_arrival_qweb'
    _description = 'Expected Arrival Report'

    def get_expected_arrival(self, property_id, arr_date, type_):
        reservation_line_obj = self.env['hms.reservation.line'].search([
            ('property_id', '=', property_id[0]), ('arrival', '=', arr_date),
            ('reservation_id.type', '=', type_)
        ])
        return reservation_line_obj

    @api.model
    def _get_report_values(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        if data is None:
            data = {}
        if not docids:
            docids = data.get('ids', data.get('active_ids'))

        property_id = data['form']['property_id']
        arr_date = data['form']['arr_date']
        type_ = data['form']['type_']
        folio_profile = self.env['hms.reservation.line'].search([
            ('property_id', '=', property_id[0]), ('arrival', '=', arr_date),
            ('reservation_id.type', '=', type_)
        ])
        # date_start = data.get('date_start', fields.Date.today())
        # date_end = data['form'].get(
        #     'date_end',
        #     str(datetime.now() +
        #         relativedelta(months=+1, day=1, days=-1))[:10])

        rm_act = self.with_context(data['form'].get('used_context', {}))
        get_expected_arrival = rm_act.get_expected_arrival(
            property_id, arr_date, type_)

        # Change Date Format to D/M/Y after all processes are done
        arr_date = datetime.strptime(arr_date, '%Y-%m-%d').strftime('%d/%m/%Y')
        return {
            'doc_ids': docids,
            'doc_model': 'hms.reservation.line',
            # 'data': data['form'],
            'arr_date': arr_date,
            'property_id': property_id[1],
            'type_': type_,
            'docs': folio_profile,
            'time': time,
            'get_expected_arrival': get_expected_arrival,
        }


# class PropertyReport(models.AbstractModel):
#     _name = 'report.property.property'

#     def get_data(self, name):
#         data_property = []
#         property_obj = self.env['property.property']
#         act_domain = [('name', '=',name)]
#         tids = property_obj.search(act_domain)
#         for data in tids:
#             data_property.append({
#                 'name': data.name,
#                 'code': data.code,
#                 'room_count': data.room_count,
#                 'roomtype_count': data.roomtype_count,
#             })
#         return data_property

#     @api.model
#     def get_report_values(self, docids, data):
#         self.model = self.env.context.get('active_model')
#         if data is None:
#             data = {}
#         if not docids:
#             docids = data['form'].get('docids')
#         property_profile = self.env['property.property'].browse(docids)
#         name = data['form'].get('name')
#         return {
#             'doc_ids': docids,
#             'doc_model': self.model,
#             'data': data['form'],
#             'docs': property_profile,
#             'time': time,
#             'property_data': self.get_data(name)
#         }
