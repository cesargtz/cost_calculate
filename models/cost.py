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
        get_bills = self.get_invoice(['in_invoice', 'in_refund'], date_range)
        bills = get_bills[0]
        bills_sale = get_bills[1]
        union = set(bills.keys()) | set(bills_sale.keys())
        keys_ordes = self.get_keys_order(union)
        # print("keys_ordes")
        # print(keys_ordes)
        # print("Totatles")
        # print(get_bills[2])
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': docs,
            'expand_invoices': docs.expand_invoices,
            'dir': bills,
            'sales': bills_sale,
            'keys_order': keys_ordes,
            'totals': get_bills[2]
        }
        return self.env['report'].render('cost_calculate.report_cost', docargs)

    @api.multi
    def get_invoice(self, types, date_range):
        purchases_invoices, sales_invoices, dir_totals = {}, {}, {}
        for single_date in date_range:
            tons = amount = cost = init_ton = init_amount = 0
            date = single_date.strftime("%Y-%m-%d")
            bills = self.reorganize(date, types) #Purchases
            dir_bill_purchase = bills[2]
            last_cost = self.env['initial.inv'].search([], order='date desc', limit=1)
            init_ton = bills[0] + last_cost.tons_daily
            init_amount = bills[1] + last_cost.amount_daily
            if init_ton > 0:
                cost = init_amount / init_ton
            inv = self.env['product.template'].search([('sum_tons_cost','=', 'True')])
            if date == inv.initial_year:
                init_ton += inv.initial_tons
                init_amount += inv.initial_import
            bills_sale = self.reorganize(date, ['out_invoice', 'out_refund']) #Sales
            dir_bill_sale = bills_sale[2]
            init_ton -= bills_sale[0]
            init_amount -= bills_sale[1]
            self.insert_inv(init_amount, init_ton, cost, date, bills[3]['tpd'], bills[3]['tpdr'],
                            bills[3]['apd'],bills[3]['apdr'],bills[3]['tsd'],bills[3]['tsdr'],
                            bills[3]['asd'],bills[3]['asdr'],bills[3]['tcr'])
            dir_totals[date] = {
                'tons': bills[3]['tpd'] - bills[3]['tpdr'],
                'total': bills[3]['apd'] - bills[3]['apdr'],
                'sum_tons': init_ton,
                'sum_import': init_amount,
                'tons_sale': bills[3]['tsd'],
                'tons_sale_ref': bills[3]['tsdr'],
                'cost': cost,
            }
            # Directorio de facturas
            if dir_bill_purchase:
                if not date in purchases_invoices:
                    purchases_invoices.update({ str(date): {} })
                purchases_invoices[str(date)] = dir_bill_purchase
            if dir_bill_sale:
                if not date in sales_invoices:
                    sales_invoices.update({ str(date): {} })
                sales_invoices[str(date)] = dir_bill_sale
        return [purchases_invoices, sales_invoices, dir_totals] #Return dir of purchases and sales invoice

    def reorganize(self, date, types):
        tons, amount, dir_keys_prd = 0, 0, {}
        daily = {'tpd': 0, 'tpdr': 0, 'apd': 0, 'apdr': 0,
            'tsd': 0, 'tsdr': 0, 'asd': 0, 'asdr': 0, 'tcr': 0, 'tcr' : 0}
        bills = self.bills(date, types)
        for bill in bills:
            product_check = self.env['account.invoice.line'].search([('invoice_id', '=', bill.id)])
            for product in product_check:
                ppp = product.product_id.product_tmpl_id
                if (ppp.calculate_cost):
                    # Suma lo comprado
                    if bill.type in ['in_invoice', 'in_refund']:
                        if bill.type == types[0]:
                            amount += bill.amount_total
                            daily['apd'] += bill.amount_total
                            if (ppp.sum_tons_cost):
                                tons += product.quantity
                                daily['tpd'] += product.quantity
                        # Resta las devolucione
                        elif bill.type == types[1]:
                            amount -= bill.amount_total
                            daily['apdr'] += bill.amount_total
                            if (ppp.sum_tons_cost):
                                tons -= product.quantity
                                daily['tpdr'] += product.quantity
                    else:
                        if (ppp.sum_tons_cost):
                            if bill.type == types[0]:
                                amount += bill.amount_total
                                tons += product.quantity
                                daily['asd'] += bill.amount_total
                                daily['tsd'] += product.quantity
                            elif bill.type == types[1]:
                                amount -= bill.amount_total
                                tons -= product.quantity
                                daily['asdr'] += bill.amount_total
                                daily['tsdr'] += product.quantity
                    obj = {
                        'number': bill.number,
                        'parner': bill.partner_id.name,
                        'date': bill.date_invoice,
                        'product': ppp.name,
                        'tons':  product.quantity,
                        'precio_unitario': product.price_unit,
                        'total': bill.amount_total,
                        'type': bill.type,
                        'sum_tons': ppp.sum_tons_cost
                    }
                    daily['tcr'] = daily['tpd'] - daily['tpdr']
                    if not str(ppp.id) in dir_keys_prd:
                            dir_keys_prd.update({str(ppp.id): []})
                    dir_keys_prd[str(ppp.id)].append(obj)
        return [tons, amount, dir_keys_prd, daily]


    def bills(self, single_date, typeinv):
            return self.env['account.invoice'].search(
                            [('type', 'in', typeinv), ('date_invoice', '=', single_date),
                            ('state', 'in', ['open', 'paid'])], order="date_invoice")

    def insert_inv(self, amount, tons, cost, date, tpd, tpdr,
                   apd, apdr, tsd, tsdr, asd, asdr, tcr):
        check = self.env['initial.inv'].search([('date', '=', date)])
        if not check:
            self.env['initial.inv'].create({
                            'amount_daily': amount, 'tons_daily': tons,
                            'cost_daily': cost, 'date': date,
                            'tpd': tpd, 'tpdr': tpdr,
                            'apd': apd, 'apdr': apdr,
                            'tsd': tsd, 'tsdr': tsdr,
                            'asd': asd, 'asdr': asdr,
                            'tcr': tcr
                        })

    def get_keys_order(self, list):
            ks = sorted(list, key=lambda x: datetime.datetime.strptime(x, '%Y-%m-%d'), reverse=True)
            return ks
