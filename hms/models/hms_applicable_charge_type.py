from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError

# Calculation Method
class HMSCalculationMethod(models.Model):
    _name = "hms.calculation.method"
    _description = "Calculation Method"
    _order = 'ordinal_no,name'

    ordinal_no = fields.Integer("Order No")
    name = fields.Char("Name")
    active = fields.Boolean("Active")

# Charge Type
class HMSChargeTypes(models.Model):
    _name = 'hms.charge_types'
    _description = "Charge Types"
    _order = 'ordinal_no,name'

    name = fields.Char("Charge Type", required=True, track_visibility=True)
    ordinal_no = fields.Integer("Ordinal No", required=True)
    calculate_method_ids = fields.Many2many("hms.calculation.method",
                                            "hms_charge_type_calculation",
                                            "charge_id", "calc_method_id",
                                            "Calculate Methods")
    active = fields.Boolean(default=True, track_visibility=True)
    _sql_constraints = [('name_unique', 'unique(name)',
                         'Charge Type is already existed.')]

    def toggle_active(self):
        for la in self:
            if not la.active:
                la.active = self.active
        super(HMSChargeTypes, self).toggle_active()


class HMSPackageChargeLine(models.Model):
    _name = 'hms.package.charge.line'
    _description = "Package Charge Line"
    _inherit = ['mail.thread']

    
    name = fields.Char("Name", required=True, track_visibility=True)
    property_id = fields.Many2one('property.property', string="Property")
    transaction_id = fields.Many2one('transaction.transaction',
                                     string='Transaction',
                                     domain="[('property_id', '=?', property_id)]")
    package_id = fields.Many2one('package.package',string="Package",track_visibility=True)
    charge_type_id = fields.Many2one("hms.charge_types",'Main Charge Type', required=True, track_visibility=True)
    calculate_method_ids = fields.Many2many( 'hms.calculation.method', "Calculation Method", related="charge_type_id.calculate_method_ids")
    calculation_method_id = fields.Many2one('hms.calculation.method',
                                            "Calculation Method",
                                            track_visibility=True,
                                            readonly=False,
                                            required=True,
                                            store=True)
    is_apply_service = fields.Boolean ('Apply Service',track_visibility=True, related='transaction_id.trans_svc')                                        
    service = fields.Float("Tax", track_visibility=True)
    is_apply_tax = fields.Boolean('Apply Tax', track_visibility=True, related='transaction_id.trans_tax')
    tax = fields.Float("Tax", track_visibility=True)
    billing_type = fields.Selection([('daily', 'Daily'),
                                    ('partial', 'Partially'),
                                    ('monthly', 'Monthly')],
                                    "Billing Type",
                                    required=True,
                                    default='daily',
                                    track_visibility=True)
    active = fields.Boolean(default=True)
#     unit_charge_line = fields.One2many("hms.unit.charge.line",
#                                        "applicable_charge_id",
#                                        "Unit Charge Line")
    use_formula = fields.Boolean("Use Formula")
    rate = fields.Float("Rate")
#     source_type_id = fields.Many2one("pms.utilities.source.type",
#                                      "Source Type")
#     is_meter = fields.Boolean("IsMeter",
#                               default=False,
#                               compute="compute_ismeter")
    _sql_constraints = [('name_uniq', 'unique (name)',
                         _("Name is exiting in the chrage applicable."))]

    # @api.onchange('charge_type_id')
    # def onchange_field_charge_type_id(self):
    #     if self.charge_type_id:
    #         for line in self.charge_type_id.calculate_method_ids:
    #             product_ids = line.ids
    #         return {
    #             'domain': {
    #                 'calculation_method_id': [('id', 'in', product_ids)]
    #             }
    #         }
    #     else:
    #         return {'domain': {'calculation_method_id': []}}

#     @api.depends('calculation_method_id')
#     def compute_ismeter(self):
#         for rec in self:
#             if rec.calculation_method_id:
#                 if rec.calculation_method_id.name == 'MeterUnit':
#                     rec.is_meter = True
#                 else:
#                     rec.is_meter = False

    # @api.model
    # def create(self, values):
    #     charge_type_id = self.search([('name', '=', values['name'])])
    #     if charge_type_id:
    #         raise UserError(_("%s is already existed" % values['name']))
    #     return super(PMSApplicableChargeType, self).create(values)

#     # @api.multi
#     # def write(self, vals):
#     #     for rec in self:
#     #         if 'name' in vals:
#     #             charge_type_id = self.search([('name', '=', vals['name'])])
#     #             if charge_type_id:
#     #                 raise UserError(_("%s is already existed" % vals['name']))
#     #     return super(PMSApplicableChargeType, self).write(vals)


# class PMSUnitChargeLine(models.Model):
#     _name = "pms.unit.charge.line"
#     _description = "Unit Charge Line"

#     name = fields.Char("Name")
#     from_unit = fields.Float("From")
#     to_unit = fields.Float("To")
#     rate = fields.Float("Rate")
#     applicable_charge_id = fields.Many2one("pms.applicable.charge.type",
#                                            'Applicable Charge Type')

#     def compute(self):
#         if self.from_unit and self.to_unit and self.rate:
#             self.name = "Rate " + str(self.rate) + "(From " + str(
#                 self.from_unit) + " Units To" + str(self.to_unit) + ")."
#         else:
#             self.name = "UNDEFINED"
