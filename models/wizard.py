# -*- coding: utf-8 -*-

from odoo import models, fields, api

class calculate_cost(models.TransientModel):
    _name = 'cost.calculate.wizard'

    date_start = fields.Date()
    date_end = fields.Date()
    expand_invoices = fields.Boolean(default=True)

    @api.multi
    def check_report(self):
        data = {}
        data['form'] = self.read(['date_start','date_end','expand_invoices'])
        return self._print_report(data)

    def _print_report(self, data):
        return self.env['report'].get_action(self,'calculate_cost.report_cost',data=data)
