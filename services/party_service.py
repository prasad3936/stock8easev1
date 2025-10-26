# services/party_service.py

from flask import Blueprint, render_template
from extensions import db
from services.stock_service import Stock

# services/party_service.py
from extensions import db

class Party(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    party_name = db.Column(db.String(120), nullable=False)
    contact_details = db.Column(db.String(255), nullable=False)
    order_status = db.Column(db.String(50), nullable=False)  # e.g., Ordered, Pending, Delivered
    order_reminder = db.Column(db.DateTime, nullable=False)

    def __init__(self, party_name, contact_details, order_status, order_reminder):
        self.party_name = party_name
        self.contact_details = contact_details
        self.order_status = order_status
        self.order_reminder = order_reminder


party_bp = Blueprint('party', __name__)

# Stock Orders Route
@party_bp.route('/orders')
def orders():
    stock_items = Stock.query.all()
    return render_template('orders.html', stock_items=stock_items)

# Reminders for Orders
@party_bp.route('/order_reminder')
def order_reminder():
    stock_items = Stock.query.filter(Stock.quantity <= 5).all()
    return render_template('order_reminder.html', stock_items=stock_items)

# Party Details Route
@party_bp.route('/details')
def party_details():
    return render_template('party_details.html')
