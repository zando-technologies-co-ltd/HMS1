import time
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from dateutil.relativedelta import relativedelta
from dateutil import parser
from odoo import api, fields, models


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
