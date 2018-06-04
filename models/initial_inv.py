# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Truck(models.AbstractModel):
    _inherit = 'report.calculate_cost.report_cost'
    _name = 'initial.inv'

    amount_daily = fields.Float()
    tons_daily = fields.Float()
    date = fields.Datetime()
