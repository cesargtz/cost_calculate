# -*- coding: utf-8 -*-

from odoo import api, fields, models


class InitialInv(models.Model):
    _name = 'initial.inv'

    name = fields.Char( required=True, select=True, copy=False, default=lambda
        self: self.env['ir.sequence'].next_by_code('code_daily_cost'), help="Unique number")

    # Sumatoria día a día
    amount_daily = fields.Float()
    tons_daily = fields.Float()
    cost_daily = fields.Float()
    date = fields.Date()

    # Diario
    tpd = fields.Float()
    tpdr = fields.Float()
    apd = fields.Float()
    apdr = fields.Float()
    tsd = fields.Float()
    tsdr = fields.Float()
    asd = fields.Float()
    asdr = fields.Float()
