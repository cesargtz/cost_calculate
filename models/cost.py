# -*- coding: utf-8 -*-
from odoo import api, models
from odoo.exceptions import UserError
import update_cost as uc
# Install pandas library
import pandas as pd
import datetime
import logging

_logger = logging.getLogger(__name__)

class ReportCalculateCost(models.AbstractModel):
    _name = 'report.calculate_cost.report_cost'

    @api.model
    def render_html(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        date_range = pd.date_range(docs.date_start, docs.date_end)
        bills_purchase = self.get_invoice(['in_invoice', 'in_refund'], date_range)

    @api.multi
    def get_invoice(self, types, date_range):
        dir_dates = {}
        for single_date in date_range:
            tons = amount = cost = init_ton = init_amount = 0
            date = single_date.strftime("%Y-%m-%d")
            bills = self.reorganize(date, types, "sum_totals") #Purchases
            last_cost = self.env['initial.inv'].search([], order='date desc', limit=1)
            init_ton = bills[0] + last_cost.tons_daily
            init_amount = bills[1] + last_cost.amount_daily
            if init_ton > 0:
                cost = init_amount / init_ton
            inv = self.env['product.template'].search([('sum_tons_cost','=', 'True')])
            if date == inv.initial_year:
                init_ton += inv.initial_tons
                init_amount += inv.initial_import
            bills = self.reorganize(date, ['out_invoice', 'out_refund'], "sum_totals") #Sales
            init_ton -= bills[0]
            init_amount -= bills[1]
            self.insert_inv(init_amount, init_ton, cost, date)

    def reorganize(self, date, types, response):
        tons, amount = 0, 0
        bills = self.bills(date, types)
        for bill in bills:
            # if not str(bill.date_invoice) in dir_dates:
            #     dir_dates.update({str(bill.date_invoice):{}})
            product_check = self.env['account.invoice.line'].search([('invoice_id', '=', bill.id)])
            for product in product_check:
                ppp = product.product_id.product_tmpl_id
                if (ppp.calculate_cost):
                    # Suma lo comprado
                    if bill.type in ['in_invoice', 'in_refund']:
                        if bill.type == types[0]:
                            amount += bill.amount_total
                            if (ppp.sum_tons_cost):
                                tons += product.quantity
                        # Resta las devolucione
                        elif bill.type == types[1]:
                            amount -= bill.amount_total
                            if (ppp.sum_tons_cost):
                                tons -= product.quantity
                    else:
                        if (ppp.sum_tons_cost):
                            if bill.type == types[0]:
                                amount += bill.amount_total
                                tons += product.quantity
                            elif bill.type == types[1]:
                                amount -= bill.amount_total
                                tons -= product.quantity
        if response == "sum_totals":
            return [tons, amount]
        elif respone == "get_dir":
            pass

    def bills(self, single_date, typeinv):
            return self.env['account.invoice'].search(
                            [('type', 'in', typeinv), ('date_invoice', '=', single_date),
                            ('state', 'in', ['open', 'paid'])], order="date_invoice")

    def insert_inv(self, amount, tons, cost, date):
        self.env['initial.inv'].create({
                        'amount_daily': amount,
                        'tons_daily': tons,
                        'cost_daily': cost,
                        'date': date
                    })
