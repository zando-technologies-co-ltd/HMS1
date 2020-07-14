# -*- coding: utf-8 -*-
# from odoo import http


# class HmsSsy(http.Controller):
#     @http.route('/hms_ssy/hms_ssy/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hms_ssy/hms_ssy/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hms_ssy.listing', {
#             'root': '/hms_ssy/hms_ssy',
#             'objects': http.request.env['hms_ssy.hms_ssy'].search([]),
#         })

#     @http.route('/hms_ssy/hms_ssy/objects/<model("hms_ssy.hms_ssy"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hms_ssy.object', {
#             'object': obj
#         })
