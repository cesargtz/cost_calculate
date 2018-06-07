# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Truck(models.Model):
    _inherit = 'report.calculate_cost.report_cost'
    _name = 'initial.inv'

    name = fields.Char( required=True, select=True, copy=False, default=lambda
        self: self.env['ir.sequence'].next_by_code('code_daily_cost'), help="Unique number")

    amount_daily = fields.Float()
    tons_daily = fields.Float()
    cost_daily = fields.Float()
    date = fields.Date()
