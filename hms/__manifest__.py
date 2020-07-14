# -*- coding: utf-8 -*-
{
    'name':
    "hms_ssy",
    'summary':
    """
        Hotel Property Management System""",
    'description':
    """
        Hotel Property Management System :
        -Reservations, Reception, Cashier, NightAudit
    """,
    'author':
    "HMS-Projects HMS, Developer Name",
    'website':
    "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category':
    'Test',
    'version':
    '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/hotel_views.xml',
        'views/hms_bank_view.xml',
        'views/hms_format_view.xml',
        'views/hms_rule_configuration_view.xml',
        'data/hms_config_data.xml',
        'views/hms_company_view.xml',
        'views/hms_users_view.xml',
        #'data/hms_country_data.xml',
        'views/hms_country_view.xml',
        'data/hms.nationality.csv',
        'data/res.country.state.csv',
        'views/hms_city_view.xml',
        'data/hms.city.csv',
        'views/hms_township_view.xml',
        'data/hms.township.csv',
        'views/hms_company_type.xml',
        'data/hms.company.category.csv',
        'data/hms.guest.category.csv',
        'views/hms_contacts_view.xml',
        #'views/views.xml',
        #'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable':
    True,
    'application':
    True,
}
