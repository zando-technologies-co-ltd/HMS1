import datetime
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class TerminateRateCateWizard(models.TransientModel):
    _name = "hms.terminate_rate_category"
    _description = "Terminate"

    def get_rate_category_id(self):
        rate_category_id = self.env['rate.categories'].browse(
            self._context.get('active_id',[])
        )
        if rate_category_id:
            return rate_category_id


    rate_category_id = fields.Many2one('rate.categories',string="Rate Code",default=get_rate_category_id,
                                     store=True, readonly=True)
    start_date = fields.Date(string="Start Date", required=True, related="rate_category_id.start_date")
    end_date = fields.Date(string="End Date", required=True)
    terminate_end_date = fields.Date(related="rate_category_id.terminate_end_date")

    def action_terminate_wiz(self):

        rate_category_id = self.env['rate.categories'].browse(
            self._context.get('active_id'))
        
        if self.terminate_end_date:
            terminate_end_date = self.terminate_end_date
            if self.end_date >= terminate_end_date:
                rate_category_id.write({'end_date': self.end_date})
            else:
                raise ValidationError(
            _("You can't set End Date before '%s'" %
                        (terminate_end_date)))
                      