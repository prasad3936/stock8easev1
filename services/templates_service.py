# services/templates_service.py

from flask import Blueprint, render_template

templates_bp = Blueprint('templates', __name__)

# Email Template
@templates_bp.route('/email')
def email_template():
    return render_template('email_template.html')

# Bill Template
@templates_bp.route('/bill')
def bill_template():
    return render_template('bill_template.html')

# Report Template
@templates_bp.route('/report')
def report_template():
    return render_template('report_template.html')
