from odoo import api, fields, models


class PropertyReport(models.AbstractModel):
    """
        Abstract Model specially for report template.
        _name = Use prefix `report.` along with `module_name.report_name`
    """
    _name = 'report.hms.report_property_qweb'
    _description = 'Property Report'

    def get_property(self, property_id):
        property_obj = self.env['property.property'].search([('id', '=',
                                                              property_id[0])])
        return property_obj

    @api.model
    def _get_report_values(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        if data is None:
            data = {}
        if not docids:
            docids = data.get('ids', data.get('active_ids'))

        property_id = data['form']['property_id']
        folio_profile = self.env['property.property'].search([
            ('id', '=', property_id[0])
        ])

        rm_act = self.with_context(data['form'].get('used_context', {}))
        get_property = rm_act.get_property(property_id)

        return {
            'doc_ids': docids,
            'doc_model': 'property.property',
            # 'data': data['form'],
            'property_id': property_id[1],
            'docs': folio_profile,
            'get_property': get_property,
        }