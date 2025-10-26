from flask import Blueprint, jsonify, request, redirect, url_for, flash, render_template
from extensions import db
from services.billing_service import Billing
from services.account_service import Account
from sqlalchemy import func
import pywhatkit as kit
import datetime

# Initialize the Blueprint
customer_bp = Blueprint('customer_service', __name__)

# def send_whatsapp_reminder(customer_name, customer_mobile, reminder_details, total_amount_due, firm_name):
#     """
#     Sends a WhatsApp reminder message to the customer.
#     """
#     # Validate inputs
#     if not all([customer_name, customer_mobile, reminder_details, total_amount_due, firm_name]):
#         return {"status": "error", "message": "Missing required information for sending the reminder."}
#
#     # Construct the message body
#     message_body = (
#         f"Dear {customer_name},\n\n"
#         f"You have the following unpaid bills:\n{reminder_details}\n\n"
#         f"Total Amount Due: ₹{total_amount_due:.2f}\n\n"
#         f"Please make the payment at your earliest convenience.\n\n"
#         f"Regards,\nYour Store Name: {firm_name}\nPowered By Stock8Ease"
#     )
#
#     try:
#         # Send message using pywhatkit
#         kit.sendwhatmsg_instantly(f"+{customer_mobile}", message_body, wait_time=15)
#         return {"status": "success", "message": f"WhatsApp message sent to {customer_name}."}
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to send message: {str(e)}"}
@customer_bp.route('/send_whatsapp_reminder', methods=['POST'])
def send_whatsapp_reminder(customer_name, customer_mobile, reminder_details, total_amount_due, firm_name):
    """
    Generates a WhatsApp link to send a reminder message to the customer.
    """
    # Validate inputs
    if not all([customer_name, customer_mobile, reminder_details, total_amount_due, firm_name]):
        return {"status": "error", "message": "Missing required information for generating the WhatsApp link."}

    # Construct the message body
    message_body = (
        f"Dear {customer_name},\n\n"
        f"You have the following unpaid bills:\n{reminder_details}\n\n"
        f"Total Amount Due: \u20b9{total_amount_due:.2f}\n\n"
        f"Please make the payment at your earliest convenience.\n\n"
        f"Regards,\nYour Store Name: {firm_name}\nPowered By Stock8Ease"
    )

    # URL encode the message body
    from urllib.parse import quote
    encoded_message = quote(message_body)

    # Generate the WhatsApp link
    whatsapp_link = f"https://wa.me/{customer_mobile}?text={encoded_message}"

    return {"status": "success", "link": whatsapp_link}

# Route to display customer list with total unpaid bill
@customer_bp.route('/list')
def customer_list():
    """
    Displays a list of customers with their total unpaid bills.
    """
    customers = db.session.query(
        Billing.customer_name,
        Billing.customer_mobile,
        func.sum(Billing.total_price).label('total_unpaid')
    ).filter(Billing.status == 'Unpaid') \
     .group_by(Billing.customer_name, Billing.customer_mobile).all()

    return render_template('customer_list.html', customers=customers)

# Route to send reminder about unpaid bills to a customer
# Route to send reminder about unpaid bills to a customer
@customer_bp.route('/send_reminder/<customer_name>/<customer_mobile>', methods=['GET'])
def send_reminder(customer_name, customer_mobile):
    """
    Sends a WhatsApp reminder message to a customer with unpaid bills.
    Returns a JSON response without redirecting.
    """
    # Retrieve the firm name from the Account model
    firm_name = Account.query.first().firm_name

    # Get all unpaid bills for the customer
    unpaid_bills = db.session.query(Billing).filter_by(
        customer_name=customer_name, 
        customer_mobile=customer_mobile, 
        status='Unpaid'
    ).all()

    if unpaid_bills:
        # Prepare reminder details and total amount
        reminder_details = "\n".join([f"Product: {bill.product_code}, Amount: {bill.total_price}" for bill in unpaid_bills])
        total_amount_due = sum([bill.total_price for bill in unpaid_bills])

        # Send reminder via WhatsApp
        response = send_whatsapp_reminder(
            customer_name=customer_name,
            customer_mobile=customer_mobile,
            reminder_details=reminder_details,
            total_amount_due=total_amount_due,
            firm_name=firm_name  # Pass the firm name
        )
        #flash(response['status'])  # Flash the status message to display on the list page
        return redirect(url_for('customer_service.customer_list'))  # Stay on the list page

    # If no unpaid bills found, stay on the customer list page
    flash(f"No unpaid bills found for {customer_name}.")
    return redirect(url_for('customer_service.customer_list'))

