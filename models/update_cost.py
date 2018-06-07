# -*- coding: utf-8 -*-
import datetime
import pandas as pd
import cost

def update_cost(self, last_date):
    initial_cost = get_initial_inv(self)
    last_cost = self.env['initial.inv'].search([], order='date desc', limit=1)
    date_range = ''
    if last_cost:
        date_range = pd.date_range(last_cost.date, last_date)
    else:
        date_range = pd.date_range(initial_cost.initial_year, last_date)
    if len(date_range) > 1:
        calculate_initial(self, date_range)

def calculate_initial(self, date_range):
    bills_purchase = self.get_invoice(['in_invoice', 'in_refund'], date_range)
    bills_sales = self.get_invoice(['out_invoice', 'out_refund'], date_range)
    invoices = self.join(bills_purchase, bills_sales)
    dir_totals = self.get_totals(invoices)
    key = sorted(dir_totals.keys(), key=lambda x: datetime.datetime.strptime(x, '%Y-%m-%d'))
    for single in date_range:
        last_cost = self.env['initial.inv'].search([], order='date desc', limit=1)
        tons, mont, coste = 0, 0, 0
        single = single.strftime("%Y-%m-%d")
        mont = last_cost.amount_daily
        tons = last_cost.tons_daily
        if single in dir_totals:
            mont += dir_totals[single]['total']
            tons += dir_totals[single]['tons'] - dir_totals[single]['tons_sale'] + dir_totals[single]['tons_sale_ref']
        product = get_initial_inv(self)
        if single == product.initial_year:
            mont +=  product.initial_import
            tons += product.initial_tons
        coste = mont / tons
        insert_inv(self, mont, tons, coste, single)

def insert_inv(self, amount, tons, cost, date):
    self.env['initial.inv'].create({
        'amount_daily': amount,
        'tons_daily': tons,
        'cost_daily': cost,
        'date': date
    })

def get_initial_inv(self):
    inv = self.env['product.template'].search([('sum_tons_cost','=', 'True')])
    return inv
