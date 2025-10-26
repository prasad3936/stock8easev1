# services/dashboard_service.py
from flask import Blueprint, render_template,jsonify,url_for
from datetime import datetime

from sqlalchemy import func
from extensions import db
from services.stock_service import Stock
from services.billing_service import Billing
from services.reminders_service import reminders_bp
from services.account_service import Account
import pywhatkit as kit

dashboard_bp = Blueprint('dashboard', __name__)
# services/dashboard_service.py
from extensions import db

class Dashboard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stock_health = db.Column(db.String(100), nullable=False)  # e.g., Healthy, Low
    next_expiry = db.Column(db.Date, nullable=False)
    email_updates = db.Column(db.String(255), nullable=False)
    sales_target = db.Column(db.Float, nullable=False)
    sales_achieved = db.Column(db.Float, default=0.0)

    def __init__(self, stock_health, next_expiry, email_updates, sales_target, sales_achieved=0.0):
        self.stock_health = stock_health
        self.next_expiry = next_expiry
        self.email_updates = email_updates
        self.sales_target = sales_target
        self.sales_achieved = sales_achieved



# Dashboard Route
@dashboard_bp.route('/')
def index():
    total_stock_value = sum([stock.selling_price * stock.quantity for stock in Stock.query.all()])
    low_stock_items = Stock.query.filter(Stock.quantity <= 10).all()
    next_expiry_item = Stock.query.order_by(Stock.expiry).first()
    
    month_sales = Billing.query.filter(db.extract('month', Billing.timestamp) == datetime.now().month).all()
    monthly_sales = sum([bill.total_price for bill in month_sales])
    today_sales = sum([bill.total_price for bill in Billing.query.filter(db.extract('day', Billing.timestamp) == datetime.now().day).all()])
    return render_template('dashboard.html', 
                           total_stock_value=total_stock_value,
                           low_stock_items=low_stock_items,
                           next_expiry_item=next_expiry_item,
                           monthly_sales=monthly_sales,today_sales
                           =today_sales)

    return jsonify(today_sales), 200

@dashboard_bp.route('/one-purchase')
def onepurchase():
    # Fetch low stock items
    low_stock_items = Stock.query.filter(Stock.quantity <= 10).all()

    # Fetch user details from the Account model (you can change this to get based on logged-in user)
    user = Account.query.first()  # Get the first account or filter based on session if needed

    # Prepare the data to send to the template
    stock_data = [
        {
            "id": stock.id,
            "name": stock.item_name,
            "quantity": stock.quantity
        }
        for stock in low_stock_items
    ]

    # Get current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Render the template and pass the necessary data
    return render_template('purchase.html', 
                           low_stock_items=stock_data, 
                           user=user, 
                           timestamp=timestamp)




@dashboard_bp.route('/today_sales')
def today_sales():
    today_sales = sum([bill.total_price for bill in Billing.query.filter(db.extract('day', Billing.timestamp) == datetime.now().day).all()])
    
    today_profit = sum([bill.total_profit  for bill in Billing.query.filter(db.extract('day', Billing.timestamp) == datetime.now().day).all()])

    return jsonify(today_sales=today_sales,today_profit=today_profit), 200

@dashboard_bp.route('/purchase')
def purchase():
    try:
        # Fetch low stock items
        low_stock_items = Stock.query.filter(Stock.quantity <= 10).all()
        user = Account.query.first()
        # Fetch expired items
        expired_products = db.session.query(
            Stock.item_name
        ).filter(Stock.expiry <= datetime.utcnow()).all()

        # Combine low stock and expired items without duplicates
        combined_items = list(set([item.item_name for item in low_stock_items] + [product.item_name for product in expired_products]))

        return render_template('all-purchase.html', 
                               combined_items=combined_items,user=user)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route('/add-expired', methods=['POST'])
def add_expired():
    try:
        # Fetch expired products
        expired_products = db.session.query(
            Stock.item_name
        ).filter(Stock.expiry <= datetime.utcnow()).all()

        # Extract item names
        expired_items = [product.item_name for product in expired_products]

        # Fetch existing items in the combined list
        low_stock_items = Stock.query.filter(Stock.quantity <= 10).all()
        low_stock_item_names = [item.item_name for item in low_stock_items]

        # Combine both low-stock items and expired items
        combined_items = list(set(low_stock_item_names + expired_items))

        return jsonify({"message": "Expired products added", "combined_items": combined_items}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def send_whatsapp_reminder(user_phone):
    try:
        # Get low stock items
        low_stock_items = Stock.query.filter(Stock.quantity <= 10).all()
        low_stock_names = [item.item_name for item in low_stock_items]

        # Get today's sales and profit
        today_sales = sum([bill.total_price for bill in Billing.query.filter(db.extract('day', Billing.timestamp) == datetime.now().day).all()])
        today_profit = sum([bill.total_profit for bill in Billing.query.filter(db.extract('day', Billing.timestamp) == datetime.now().day).all()])

        # Get expired products
        expired_products = db.session.query(Stock.item_name).filter(Stock.expiry <= datetime.utcnow()).all()
        expired_item_names = [product.item_name for product in expired_products]

        # Prepare the message content
        message_content = f"Reminder: \n\n"
        message_content += f"Limited Stock Items: {', '.join(low_stock_names)}\n" if low_stock_names else "No limited stock items.\n"
        message_content += f"Today's Sales: ${today_sales:.2f}\n"
        message_content += f"Today's Profit: ${today_profit:.2f}\n"
        message_content += f"Expired Items: {', '.join(expired_item_names)}\n" if expired_item_names else "No expired items.\n"

        # Send WhatsApp message using PyWhatKit (to the user's phone)
        kit.sendwhatmsg(f"+{user_phone}", message_content, datetime.now().hour, datetime.now().minute + 2)  # Sends message 2 minutes from now

        return {"message": "Reminder sent successfully"}, 200

    except Exception as e:
        return {"error": str(e)}, 500
    
@dashboard_bp.route('/send-reminder', methods=['POST' , 'GET'])
def send_dashboard_reminder():
    try:
        # Get user phone number (ensure your model has this attribute)
        user = Account.query.first()  # Modify based on your model and logic
        user_phone = Account.mobile  # Assuming the user has a phone attribute

        # Send WhatsApp reminder
        response, status = send_whatsapp_reminder(user_phone)
        
        return jsonify(response,user_phone), status

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_total_profit():
    total_profit = db.session.query(func.sum(Billing.total_profit)) \
        .filter(Billing.status == 'Paid') \
        .scalar()
    return total_profit or 0  # Return 0 if result is None

from flask import jsonify

@dashboard_bp.route('/total_profit')
def total_profit_view():
    profit = get_total_profit()
    return jsonify({"total_profit": profit or 0})