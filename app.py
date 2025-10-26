from flask import Flask, render_template, redirect, url_for, request, session
import threading
import webview
from extensions import db
from flask_basicauth import BasicAuth
from flask_sqlalchemy import SQLAlchemy
from services.stock_service import stock_bp
from services.billing_service import billing_bp
from services.reports_service import reports_bp
from services.reminders_service import reminders_bp
from services.templates_service import templates_bp
from services.account_service import account_bp
from services.dashboard_service import dashboard_bp
from services.party_service import party_bp
from services.staff_service import staff_bp
from services.customer_service import customer_bp

# Initialize the Flask app
app = Flask(__name__)

# Basic Authentication configuration
app.config['BASIC_AUTH_USERNAME'] = 'admin'
app.config['BASIC_AUTH_PASSWORD'] = 'admin'
app.secret_key = 'your_secret_key'

# Configure Database URI (MySQL)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://#USER:PASS@mysql-1f761a7d-prasadcpatil246-f8f0.b.aivencloud.com:14627/inventorydb'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:admin@localhost/inventory_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db.init_app(app)

# Initialize BasicAuth
basic_auth = BasicAuth(app)

# Register Blueprints for different services
app.register_blueprint(stock_bp, url_prefix='/stock')
app.register_blueprint(billing_bp, url_prefix='/billing')
app.register_blueprint(reports_bp, url_prefix='/reports')
app.register_blueprint(reminders_bp, url_prefix='/reminders')
app.register_blueprint(templates_bp, url_prefix='/templates')
app.register_blueprint(account_bp, url_prefix='/account')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(party_bp, url_prefix='/party')
app.register_blueprint(staff_bp, url_prefix='/staff')
app.register_blueprint(customer_bp, url_prefix='/customers')


@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == app.config['BASIC_AUTH_USERNAME'] and password == app.config['BASIC_AUTH_PASSWORD']:
            return redirect(url_for('dashboard.index'))
        return "Invalid credentials", 401
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Remove the user from the session
    session.pop('username', None)
    return redirect(url_for('login'))

def run_flask():
    # Run the Flask application in debug mode, and disable the reloader
    app.run(debug=True, use_reloader=False)  # Disables the reloader when running in a background thread

# Launch Flask app in a separate thread
def start_flask_thread():
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True  # Ensure the thread exits when the main program exits
    flask_thread.start()

# WebView integration using PyWebView
if __name__ == '__main__':
    start_flask_thread()  # Start Flask in a separate thread

    # Launch PyWebView and load Flask app in a window
    webview.create_window('Stock8Ease - A Complete Inventory Solution ', 'http://127.0.0.1:5000', width=800, height=600)

    # Start the PyWebView main loop
    webview.start()
