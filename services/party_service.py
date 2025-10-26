from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from extensions import db
from services.stock_service import Stock
from services.billing_service import Billing
from datetime import datetime

# Define the Party model
class Party(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    party_name = db.Column(db.String(120), nullable=False)
    firm_name = db.Column(db.String(120), nullable=False)
    contact_details = db.Column(db.String(255), nullable=False)
    order_status = db.Column(db.String(50), nullable=False)
    order_reminder = db.Column(db.DateTime, nullable=False)

    def __init__(self, party_name, firm_name, contact_details, order_status, order_reminder):
        self.party_name = party_name
        self.firm_name = firm_name
        self.contact_details = contact_details
        self.order_status = order_status
        self.order_reminder = order_reminder

# Initialize Blueprint
party_bp = Blueprint('party', __name__)

# Party Details Page
@party_bp.route('/details')
def party_details():
    parties = Party.query.order_by(Party.party_name).all()
    return render_template('party_details.html', parties=parties)

# Add Party
@party_bp.route('/add_party', methods=['POST'])
def add_party():
    data = request.form
    new_party = Party(
        party_name=data['party_name'],
        firm_name=data['firm_name'],
        contact_details=data['contact_details'],
        order_status=data['order_status'],
        order_reminder=datetime.strptime(data['order_reminder'], "%Y-%m-%dT%H:%M")
    )
    db.session.add(new_party)
    db.session.commit()
    flash("Party added successfully.")
    return redirect(url_for('party.party_details'))

# Delete Party
@party_bp.route('/delete_party/<int:party_id>', methods=['POST'])
def delete_party(party_id):
    party = Party.query.get(party_id)
    if party:
        db.session.delete(party)
        db.session.commit()
        flash("Party deleted.")
    else:
        flash("Party not found.")
    return redirect(url_for('party.party_details'))

# AJAX Search for Party
@party_bp.route('/search_party')
def search_party():
    query = request.args.get('q', '')
    results = Party.query.filter(Party.party_name.ilike(f"%{query}%")).all()
    return jsonify([
        {"id": party.id, "text": party.party_name,"mobile": party.contact_details}
        for party in results
    ])

# Party Payment Summary
@party_bp.route('/party_list')
def party_list():
    parties = Party.query.order_by(Party.party_name).all()
    party_data = []

    for party in parties:
        unpaid_total = db.session.query(db.func.sum(Billing.total_price)) \
            .filter(Billing.customer_name == party.party_name, Billing.status == 'Unpaid') \
            .scalar() or 0

        paid_total = db.session.query(db.func.sum(Billing.total_price)) \
            .filter(Billing.customer_name == party.party_name, Billing.status == 'Paid') \
            .scalar() or 0

        status = "Paid" if unpaid_total == 0 else "Unpaid"

        party_data.append({
            "id": party.id,
            "name": party.party_name,
            "firm": party.firm_name,
            "contact": party.contact_details,
            "status": status,
            "remaining": unpaid_total
        })

    return render_template('party.html', party_data=party_data)