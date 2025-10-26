# services/reminders_service.py

from flask import Blueprint, render_template
from datetime import datetime, timedelta
from extensions import db
from services.stock_service import Stock

reminders_bp = Blueprint('reminders', __name__)
# services/reminders_service.py
from extensions import db

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False)
    reminder_type = db.Column(db.String(50), nullable=False)  # e.g., Expiry, Stock level
    reminder_message = db.Column(db.String(255), nullable=False)
    reminder_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), default="Pending")  # e.g., Pending, Completed

    stock = db.relationship('Stock', backref=db.backref('reminders', lazy=True))

    def __init__(self, stock_id, reminder_type, reminder_message, reminder_date, status="Pending"):
        self.stock_id = stock_id
        self.reminder_type = reminder_type
        self.reminder_message = reminder_message
        self.reminder_date = reminder_date
        self.status = status


    stock = db.relationship('Stock', backref=db.backref('reminders', lazy=True))

# Check for Expiry Reminders
@reminders_bp.route('/expiry_reminder')
def expiry_reminder():
    today = datetime.today()
    expiry_date = today + timedelta(days=7)
    stock_items = Stock.query.filter(
        Stock.expiry <= expiry_date.strftime('%Y-%m-%d')
    ).all()

    return render_template('expiry_reminder.html', stock_items=stock_items)

# Check for Low Stock Reminders
@reminders_bp.route('/low_stock_reminder')
def low_stock_reminder():
    stock_items = Stock.query.filter(Stock.quantity <= 10).all()
    return render_template('low_stock_reminder.html', stock_items=stock_items)

# Rules for Reminders
@reminders_bp.route('/rules')
def reminder_rules():
    rules = """
    1. Expiry reminders are triggered for items expiring in the next 7 days.
    2. Low stock reminders are triggered for items with quantity <= 10.
    """
    return render_template('reminder_rules.html', rules=rules)
