# services/reports_service.py
import calendar
from flask import Blueprint, render_template
from datetime import datetime
from extensions import db
from services.billing_service import Billing
from services.stock_service import Stock

reports_bp = Blueprint('reports', __name__)
class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.String(20), nullable=False)
    year = db.Column(db.String(4), nullable=False)
    total_sales = db.Column(db.Float, nullable=False)
    profit = db.Column(db.Float, nullable=False)


# Monthly Sales Report
@reports_bp.route('/monthly_sales')
def monthly_sales_report():
    month = datetime.now().month
    year = datetime.now().year
    bills = Billing.query.filter(
        db.extract('month', Billing.timestamp) == month,
        db.extract('year', Billing.timestamp) == year
    ).all()

    total_sales = sum([bill.total_price for bill in bills])

    return render_template('monthly_sales_report.html', total_sales=total_sales, month=month, year=year)

# Annual Sales Report
@reports_bp.route('/annual_sales')
def annual_sales_report():
    year = datetime.now().year
    bills = Billing.query.filter(db.extract('year', Billing.timestamp) == year).all()

    total_sales = sum([bill.total_price for bill in bills])

    return render_template('annual_sales_report.html', total_sales=total_sales, year=year)

# Profit Report
@reports_bp.route('/monthly_profit')
def monthly_profit_report():
    month = datetime.now().month
    year = datetime.now().year
    bills = Billing.query.filter(
        db.extract('month', Billing.timestamp) == month,
        db.extract('year', Billing.timestamp) == year
    ).all()

    profit = 0
    for bill in bills:
        stock_item = Stock.query.filter_by(product_code=bill.product_code).first()
        if stock_item:
            profit += (bill.total_price - stock_item.price * bill.quantity)

    
    # Monthly Profit Calculation
    monthly_profit = 0
    for bill in bills:
        stock_item = Stock.query.filter_by(product_code=bill.product_code).first()
        if stock_item:
            monthly_profit += (bill.total_price - stock_item.price * bill.quantity)

    return render_template('monthly_profit_report.html', profit=profit,monthly_profit=monthly_profit, month=month, year=year)

@reports_bp.route('/profit')
def profit_report():
    month = datetime.now().month
    year = datetime.now().year
    bills = Billing.query.filter(
        db.extract('month', Billing.timestamp) == month,
        db.extract('year', Billing.timestamp) == year
    ).all()
    
    profit = 0
    for bill in bills:
        stock_item = Stock.query.filter_by(product_code=bill.product_code).first()
        if stock_item:
            profit += (bill.total_price - stock_item.price * bill.quantity)

    return render_template('profit_report.html', profit=profit, month=month, year=year)

@reports_bp.route('/all_sales')
def all_sales_report():
    # Get current month and year
    month = datetime.now().month
    year = datetime.now().year

    # Convert month number to month name
    month_name = calendar.month_name[month]  # e.g., "January", "February", etc.
    
    # Monthly Sales Calculation
    monthly_bills = Billing.query.filter(
        db.extract('month', Billing.timestamp) == month,
        db.extract('year', Billing.timestamp) == year
    ).all()

    total_sales_monthly = sum([bill.total_price for bill in monthly_bills])

    # Annual Sales Calculation
    annual_bills = Billing.query.filter(db.extract('year', Billing.timestamp) == year).all()
    total_sales_annual = sum([bill.total_price for bill in annual_bills])

    # Monthly Profit Calculation
    monthly_profit = 0
    for bill in monthly_bills:
        stock_item = Stock.query.filter_by(product_code=bill.product_code).first()
        if stock_item:
            monthly_profit += (bill.total_price - stock_item.price * bill.quantity)

    # Total Profit Calculation (for all time)
    total_profit = 0
    all_bills = Billing.query.all()
    for bill in all_bills:
        stock_item = Stock.query.filter_by(product_code=bill.product_code).first()
        if stock_item:
            total_profit += (bill.total_price - stock_item.price * bill.quantity)

    # Total Sales from Billing (without filter)
    total_sales_billing = sum([bill.total_price for bill in Billing.query.all()])

    return render_template(
        'reports.html',
        month=month_name,  # Passing the month name
        year=year,
        total_sales_monthly=total_sales_monthly,
        total_sales_annual=total_sales_annual,
        profit=monthly_profit,  # Monthly Profit
        total_sales_billing=total_sales_billing,
        total_profit=total_profit  # Total Profit
    )

@reports_bp.route('/total_sales')
def total_sales_report():
    total_sales = sum([bill.total_price for bill in Billing.query.all()])
    return render_template('total_sales_report.html', total_sales=total_sales)