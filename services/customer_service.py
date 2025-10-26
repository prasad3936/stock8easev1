from flask import Blueprint, jsonify, request, redirect, url_for, flash, render_template
from extensions import db
from services.billing_service import Billing
from services.account_service import Account
from sqlalchemy import func
import pywhatkit as kit
import datetime

# Initialize the Blueprint
customer_bp = Blueprint('customer_service', __name__)

# Helper function to send WhatsApp message
def send_whatsapp_message(customer_name, customer_mobile, reminder_details, total_amount_due, firm_name):
    """
    Sends a WhatsApp reminder message to the customer.
    """
    if not all([customer_name, customer_mobile, reminder_details, total_amount_due, firm_name]):
        return {"status": "error", "message": "Missing required information for sending the reminder."}

    message_body = (
        f"Dear {customer_name},\n\n"
        f"You have the following unpaid bills:\n{reminder_details}\n\n"
        f"Total Amount Due: ₹{total_amount_due:.2f}\n\n"
        f"Please make the payment at your earliest convenience.\n\n"
        f"Regards,\nYour Store Name: {firm_name}\nPowered By Stock8Ease"
    )

    try:
        kit.sendwhatmsg_instantly(f"+{customer_mobile}", message_body, wait_time=15)
        return {"status": "success", "message": f"WhatsApp message sent to {customer_name}."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to send message: {str(e)}"}

# Route to display customer list with total unpaid bill
@customer_bp.route('/list')
def customer_list():
    customers = db.session.query(
        Billing.customer_name,
        Billing.customer_mobile,
        func.sum(Billing.total_price).label('total_unpaid')
    ).filter(Billing.status == 'Unpaid') \
     .group_by(Billing.customer_name, Billing.customer_mobile).all()

    return render_template('customer_list.html', customers=customers)

# Route to send reminder about unpaid bills to a customer
@customer_bp.route('/send_reminder/<customer_name>/<customer_mobile>', methods=['GET'])
def send_reminder(customer_name, customer_mobile):
    firm_name = Account.query.first().firm_name

    unpaid_bills = db.session.query(Billing).filter_by(
        customer_name=customer_name,
        customer_mobile=customer_mobile,
        status='Unpaid'
    ).all()

    if unpaid_bills:
        reminder_details = "\n".join([
            f"Product: {bill.product_code}, Amount: {bill.total_price}"
            for bill in unpaid_bills
        ])
        total_amount_due = sum([bill.total_price for bill in unpaid_bills])

        response = send_whatsapp_message(
            customer_name=customer_name,
            customer_mobile=customer_mobile,
            reminder_details=reminder_details,
            total_amount_due=total_amount_due,
            firm_name=firm_name
        )

        flash(response['message'])  # Optional: show status message
        return redirect(url_for('customer_service.customer_list'))

    flash(f"No unpaid bills found for {customer_name}.")
    return redirect(url_for('customer_service.customer_list'))