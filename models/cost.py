# -*- coding: utf-8 -*-

from odoo import api, models
from odoo.exceptions import UserError
import update_cost as uc
# Install pandas library 2
import pandas as pd
import datetime
import logging

_logger = logging.getLogger(__name__)


class ReportCalculateCost(models.AbstractModel):
    _name = 'report.calculate_cost.report_cost'

    @api.model
    def render_html(self, docids, data=None):
            self.model = self.env.context.get('active_model')
            docs = self.env[self.model].browse(
                self.env.context.get('active_id'))
            date_range = pd.date_range(docs.date_start, docs.date_end)
            uc.update_cost(self, docs.date_end)
            bills = self.get_invoice(
                ['in_invoice', 'in_refund'], date_range)
            bills_sale = self.get_invoice(
                ['out_invoice', 'out_refund'], date_range)
            invoices = self.join(bills, bills_sale)
            dir_totals = self.get_totals(invoices)
            keys_ordes = self.get_keys_order(bills)
            docargs = {
                'doc_ids': self.ids,
                'doc_model': self.model,
                'docs': docs,
                'expand_invoices': docs.expand_invoices,
                'dir': bills,
                'sales': bills_sale,
                'keys_order': keys_ordes,
                'totals': dir_totals
            }
            return self.env['report'].render('cost_calculate.report_cost', docargs)

    @api.multi
    def get_invoice(self, types, date_range):
            dir_dates = {}
            tons = 0
            date_range = date_range
            for single_date in date_range:
                    date = single_date.strftime("%Y-%m-%d")
                    bills = self.bills(date, types)
                    for bill in bills:
                            if not str(bill.date_invoice) in dir_dates:
                                    dir_dates.update(
                                        {str(bill.date_invoice): {}})
                            product_check = self.env['account.invoice.line'].search(
                                [('invoice_id', '=', bill.id)])
                            for product in product_check:
                                    ppp = product.product_id.product_tmpl_id
                                    if (ppp.calculate_cost):
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
                                            # 'total': product.price_subtotal,
                                            if not str(ppp.id) in dir_dates[bill.date_invoice]:
                                                    dir_dates[bill.date_invoice].update(
                                                        {str(ppp.id): []})
                                            dir_dates[bill.date_invoice][str(
                                                ppp.id)].append(obj)
            return dir_dates

    def bills(self, single_date, typeinv):
            return self.env['account.invoice'].search(
                            [('type', 'in', typeinv), ('date_invoice', '=', single_date),
                            ('state', 'in', ['open', 'paid'])], order="date_invoice")

    def get_keys_order(self, dir):
            k = dir.keys()
            ks = sorted(k, key=lambda x: datetime.datetime.strptime(
                        x, '%Y-%m-%d'), reverse=True)
            return ks

    def get_totals(self, facturas):
            dir_totals = {}
            keys = facturas.keys()
            # print(keys)
            sum_tons_total = sum_import_total = cost = 0
            initial = True
            inv = self.env['product.template'].search([('sum_tons_cost','=', 'True')])
            for order in sorted(keys, key=lambda x: datetime.datetime.strptime(x, '%Y-%m-%d')):
                    sum_tot, tons, const = 0, 0 ,0
                    dir_totals.update({str(order): {}})
                    for proudct in facturas[order]:
                            for i in facturas[order][proudct]:
                                    # Siempre se suma el importe.
                                    if i['type'] == 'in_invoice':
                                            sum_tot += i['total']
                                            if i['sum_tons']:  # Suma solo las toneladas de maiz
                                                    tons += i['tons']
                                    if i['type'] == 'in_refund':  # Devolucione
                                            sum_tot -= i['total']
                                            if i['sum_tons']:
                                                    tons -= i['tons']
                    dir_totals[order].update({
                        'tons': tons,
                        'total': sum_tot,
                    })
            for order in sorted(keys, key=lambda x: datetime.datetime.strptime(x, '%Y-%m-%d')):
                    if inv.initial_year == order:
                        sum_tons_total += inv.initial_tons
                        sum_import_total += inv.initial_import
                        initial = False
                    if initial:
                        sum_tons_total += inv.initial_tons
                        sum_import_total += inv.initial_import
                        initial = False
                    # suma toneladas por día
                    sum_tons_total += dir_totals[order]['tons']
                    sum_import_total += dir_totals[order]['total']
                    # El costo se calcula antes del calculo de facturas
                    if sum_tons_total > 0:
                            cost = float(sum_import_total / sum_tons_total)
                    sales = self.get_sales(order)
                    sum_tons_total -= sales[0]
                    sum_import_total -= sales[1]
                    dir_totals[order].update({
                        'tons': dir_totals[order]['tons'],
                        'total': dir_totals[order]['total'],
                        'sum_tons': sum_tons_total,
                        'sum_import': sum_import_total,
                        'tons_sale': sales[2],
                        'tons_sale_ref': sales[3],
                        'cost': cost,
                    })
            return dir_totals

    def get_sales(self, date):
            invoices = self.bills(date, ['out_invoice', 'out_refund'])
            tons, total, tons_sale, tons_ref = 0, 0, 0, 0
            for invoice in invoices:
                    product_check = self.env['account.invoice.line'].search(
                                            [('invoice_id', '=', invoice.id)])
                    for line in product_check:
                            ppp = line.product_id.product_tmpl_id
                            if ppp.sum_tons_cost:
                                    if invoice['type'] == 'out_invoice':
                                            tons_sale += line.quantity #Toneladas totales
                                            tons += line.quantity # Tons reales
                                            total += line.price_subtotal
                                    if invoice['type'] == 'out_refund':
                                            tons_ref += line.quantity
                                            tons -= line.quantity
                                            total -= line.price_subtotal
            return([tons, total, tons_sale, tons_ref])

    def join(self, purchase, sale):
            for date in sale:
                    if not date in purchase:
                            purchase.update({str(date): {}})
                    for item in sale[date]:
                            # print(item)
                            if not item in purchase[date]:
                                    purchase[date].update({str(item): []})
                            purchase[date][item].append(
                                sale[date][item][0])
            # _logger.critical(purchase)
            return purchase
