# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Truck(models.Model):
    _inherit = 'report.calculate_cost.report_cost'
    _name = 'initial.inv'

    name = fields.Char( required=True, select=True, copy=False, default=lambda
        self: self.env['ir.sequence'].next_by_code('code_daily_cost'), help="Unique number")

    # Sumatoria día a día
    amount_daily = fields.Float()
    tons_daily = fields.Float()
    cost_daily = fields.Float()
    date = fields.Date()

    # Diario
    tpd = fields.Float(string="Tns compra")
    tpdr = fields.Float(string="Dev tons compra")
    apd = fields.Float(string="Monto compra")
    apdr = fields.Float(string="Monto de NC compra")
    tsd = fields.Float(string="Tns venta")
    tsdr = fields.Float(string="Tns de NC venta")
    asd = fields.Float(string="Monto de venta")
    asdr = fields.Float(string="Dev tons venta")
