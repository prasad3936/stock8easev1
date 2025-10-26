from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
from extensions import db
from sqlalchemy import func
from services.stock_service import Stock
from uuid import uuid4

billing_bp = Blueprint('billing', __name__)

# Define the Billing model
class Billing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid4()))  # Unique bill ID
    customer_name = db.Column(db.String(100), nullable=False)
    customer_mobile = db.Column(db.String(15), nullable=False)
    product_code = db.Column(db.String(10), db.ForeignKey('stock.product_code'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    total_profit = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(10), default='unpaid')
    product = db.relationship('Stock', backref=db.backref('billings', lazy=True))

from datetime import datetime

def generate_bill_id():
    try:
        now = datetime.utcnow()
        year = now.year
        month = now.month

        # Count bills for the current month using the `timestamp` field
        current_month_bills = Billing.query.filter(
            db.extract('year', Billing.timestamp) == year,
            db.extract('month', Billing.timestamp) == month
        ).count()

        # Generate bill ID with format: BYYYYMMNN
        return f"{year}{month:02}{current_month_bills + 1:02}"
    except Exception as e:
        print(f"Error generating bill ID: {e}")
        raise




@billing_bp.route('/create', methods=['GET', 'POST'])
def create_bill():
    if request.method == 'POST':
        customer_name = request.form['customer_name']
        customer_mobile = request.form['customer_mobile']
        status = 'Paid' if request.form.get('status') == 'on' else 'Unpaid'
        product_codes = request.form.getlist('product_code')
        quantities = request.form.getlist('quantity')

        if len(product_codes) != len(quantities):
            return 'Mismatch between product codes and quantities', 400

        total_price = 0
        total_profit = 0
        bills = []

        for i, product_code in enumerate(product_codes):
            product = Stock.query.filter_by(product_code=product_code).first()
            if product:
                quantity = int(quantities[i])
                if product.quantity >= quantity:
                    product_total_price = product.selling_price * quantity
                    product_total_profit = (product.selling_price - product.price) * quantity

                    total_price += product_total_price
                    total_profit += product_total_profit

                    # Generate the custom bill_id
                    bill_id = generate_bill_id()

                    new_bill = Billing(
                        bill_id=bill_id,
                        customer_name=customer_name,
                        customer_mobile=customer_mobile,
                        product_code=product_code,
                        quantity=quantity,
                        total_price=product_total_price,
                        total_profit=product_total_profit,
                        status=status
                    )
                    bills.append(new_bill)
                    product.quantity -= quantity
                else:
                    return f'Not enough stock available for product {product_code}', 400
            else:
                return f'Product {product_code} not found', 404

        # Add all new bills and commit them to the database
        for bill in bills:
            db.session.add(bill)
        db.session.commit()

        # Send bills and totals to the template
        return render_template(
            'bill_template.html',
            bills=bills,
            bill_id=bill_id,
            total_price=total_price,
            total_profit=total_profit
        )

    # Render the form with available product codes
    product_codes = Stock.query.with_entities(Stock.product_code).all()
    return render_template('create_bill.html', product_codes=product_codes)

# Existing Monthly Sales Route
@billing_bp.route('/monthly', methods=['GET'])
def monthly_sales():
    try:
        monthly_sales_data = db.session.query(
            func.extract('year', Billing.timestamp).label('year'),
            func.extract('month', Billing.timestamp).label('month'),
            func.sum(Billing.total_price).label('total_sales')
        ).group_by(
            func.extract('year', Billing.timestamp),
            func.extract('month', Billing.timestamp)
        ).order_by(
            func.extract('year', Billing.timestamp).desc(),
            func.extract('month', Billing.timestamp).desc()
        ).all()

        monthly_sales_list = [
            {'year': int(year), 'month': int(month), 'total_sales': total_sales}
            for year, month, total_sales in monthly_sales_data
        ]
        
        return jsonify(monthly_sales_list), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



# New Route for Top Selling Products
@billing_bp.route('/top-selling-products', methods=['GET'])
def top_selling_products():
    try:
        # Join Billing with Stock to get product names along with product code
        top_products = db.session.query(
            Billing.product_code,
            Stock.item_name,  # Add product name from the Stock table
            func.sum(Billing.quantity).label('total_quantity'),
            func.sum(Billing.total_price).label('total_sales')
        ).join(Stock, Billing.product_code == Stock.product_code)  # Join on product_code

        # Group by both product_code and product_name
        top_products = top_products.group_by(Billing.product_code, Stock.item_name)

        # Order by total sales (highest first)
        top_products = top_products.order_by(func.sum(Billing.total_price).desc())

        # Limit to top 5 results
        top_products = top_products.limit(5).all()

        # Convert the results to a list of dictionaries
        top_products_list = [{
            'product_code': product_code,
            'product_name': item_name,  # Include the product name
            'total_quantity': total_quantity,
            'total_sales': total_sales
        } for product_code, item_name, total_quantity, total_sales in top_products]

        return jsonify(top_products_list), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



# New Route for Next Expiry Product
@billing_bp.route('/next-expiry', methods=['GET'])
def next_expiry():
    try:
        next_expiry_product = db.session.query(
            Stock.item_name, Stock.expiry
        ).filter(Stock.expiry > datetime.utcnow()).order_by(Stock.expiry.asc()).first()

        if next_expiry_product:
            return jsonify({
                'product_name': next_expiry_product.item_name,
                'expiry_date': next_expiry_product.expiry,
                'link': url_for('stock.view_stock')  # Replace with your actual stock page URL
            }), 200
        else:
            return jsonify({'message': 'No upcoming expiry products found'}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# New Route for Limited Stock Items (Stock <= 10)
@billing_bp.route('/limited-stock', methods=['GET'])
def limited_stock():
    try:
        limited_stock_items = db.session.query(
            Stock.product_name, Stock.quantity
        ).filter(Stock.quantity <= 10).all()

        limited_stock_list = [{
            'product_name': product_name,
            'stock_quantity': quantity
        } for product_name, quantity in limited_stock_items]

        return jsonify(limited_stock_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@billing_bp.route('/search_customer', methods=['GET'])
def search_customer():
    query = request.args.get('query', '')
    customers = Billing.query.filter(Billing.customer_name.ilike(f'%{query}%')).with_entities(Billing.customer_name, Billing.customer_mobile).all()
    results = [{"customer_name": customer.customer_name, "customer_mobile": customer.customer_mobile} for customer in customers]
    return jsonify(results)

@billing_bp.route('/get_customer')
def get_customer():
    query = request.args.get('query', '').strip()
    if not query:
        return jsonify([])  # Return an empty list if no query

    # Fetch customers matching the query
    customers = Billing.query.filter(Billing.name.ilike(f"%{query}%")).all()

    # Format the response
    response = [
        {"customer_name": customer.name, "customer_mobile": customer.mobile}
        for customer in customers
    ]
    return jsonify(response)





@billing_bp.route('/update_status/<string:bill_id>', methods=['POST'])
def update_status(bill_id):
    try:
        # Fetch all bills with the given bill_id
        bills = Billing.query.filter_by(bill_id=bill_id).all()
        if not bills:
            return jsonify(success=False, message="Bill not found"), 404

        # Update the status for all bills with the same bill_id
        new_status = request.form.get('status')  # 'Paid' or 'Unpaid'
        for bill in bills:
            bill.status = new_status

        db.session.commit()
        return jsonify(success=True), 200
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=str(e)), 500

# Route to view all bills with product codes and names
@billing_bp.route('/all')
def view_all_bills():
    """Route to display all billing records."""
    
    # Query all bills
    bills = Billing.query.all()
    
    # Group bills by bill_id and aggregate products and totals
    grouped_bills = {}
    for bill in bills:
        # If the bill_id is not already in the grouped_bills dictionary, add it
        if bill.bill_id not in grouped_bills:
            grouped_bills[bill.bill_id] = {
                'products': [],
                'total_price': 0,
                'timestamp': bill.timestamp,
                'customer_name': bill.customer_name,
                'customer_mobile': bill.customer_mobile,
                'status': bill.status,
            }
        
        # Fetch product details from Stock table
        product = Stock.query.filter_by(product_code=bill.product_code).first()
        product_name = product.item_name if product else 'Unknown Product'
        
        # Append product code, name, and quantity to the products list
        grouped_bills[bill.bill_id]['products'].append({
            'product_code': bill.product_code,
            'product_name': product_name,
            'quantity': bill.quantity,
            'total_price': bill.total_price
        })
        
        # Accumulate the total price for this bill
        grouped_bills[bill.bill_id]['total_price'] += bill.total_price
    
    return render_template('view_all_bills.html', bills=grouped_bills)


# Route to delete all bills
@billing_bp.route('/delete_all', methods=['POST'])
def delete_all_bills():
    try:
        # Delete all bills from the database
        Billing.query.delete()
        db.session.commit()
        return redirect(url_for('billing.view_all_bills'))  # Redirect to view all bills after deletion
    except Exception as e:
        db.session.rollback()
        return f"An error occurred while deleting bills: {e}", 500

# Route to view a single bill
@billing_bp.route('/view/<int:bill_id>')
def view_bill(bill_id):
    """Route to display a single bill's details."""
    # Fetch all Billing records for the given bill_id
    bill_records = Billing.query.filter_by(bill_id=bill_id).all()

    if not bill_records:
        # If no records are found, return a 404
        return f"Bill with ID {bill_id} not found", 404

    # Prepare the detailed data for rendering
    bills = []
    for bill in bill_records:
        # Fetch the product name from Stock using the product_code
        product = Stock.query.filter_by(product_code=bill.product_code).first()
        item_name = product.item_name if product else "Unknown Product"

        bills.append({
            "customer_name": bill.customer_name,
            "customer_mobile": bill.customer_mobile,
            "product_code": bill.product_code,
            "item_name": item_name,
            "quantity": bill.quantity,
            "total_price": bill.total_price,
            "status": bill.status,
            "timestamp": bill.timestamp,
        })

    # Calculate the total price for all items in the bill
    total_price = sum(item["total_price"] for item in bills)

    # Render the template with the required context
    return render_template('bill_template.html', bills=bills, total_price=total_price, bill_id=bill_id)



# Route to delete a single bill
@billing_bp.route('/delete/<int:bill_id>', methods=['POST'])
def delete_bill(bill_id):
    """Route to delete a single bill by ID."""
    bill = Billing.query.get_or_404(bill_id)  # Fetch the bill by ID or return 404 if not found
    db.session.delete(bill)  # Delete the bill
    db.session.commit()  # Commit the transaction to the database

    # Redirect to the view all bills page
    return redirect(url_for('billing.view_all_bills'))


# New Route for Total Sales (Sum of all bills' total price)
@billing_bp.route('/total-sales', methods=['GET'])
def total_sales():
    try:
        # Query the sum of all total_price values from the Billing table
        total_sales = db.session.query(
            func.sum(Billing.total_price).label('total_sales')
        ).scalar()

        return jsonify({'total_sales': total_sales or 0}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# New Route for Total Sales (Sum of all bills' total price)
@billing_bp.route('/total-profit', methods=['GET'])
def total_profit():
    try:
        # Query the sum of all total_price values from the Billing table
        total_profit = db.session.query(
            func.sum(Stock.price).label('total_profit')
        ).scalar()

        return jsonify({'total_profit': total_profit or 0}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@billing_bp.route('/expired-items', methods=['GET'])
def expired_items():
    try:
        current_date = datetime.utcnow()

        # Query for expired items
        expired_products = db.session.query(
            Stock.item_name, Stock.expiry
        ).filter(Stock.expiry <= current_date).all()

        if expired_products:
            expired_list = [
                {
                    'item_name': product.item_name,
                    'expiry_date': product.expiry,
                    'link': url_for('stock.view_stock')  # Replace with the actual URL
                } for product in expired_products
            ]
            return render_template('expired_products.html', expired_items=expired_list), 200
        else:
            return render_template('expired_products.html', expired_items=[]), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@billing_bp.route('/due', methods=['GET'])
def due():
    try:
        # Query the sum of all total_price values from unpaid bills
        total_due = db.session.query(
            func.sum(Billing.total_price).label('total_due')
        ).filter(Billing.status == 'unpaid').scalar()

        return jsonify({'total_due': total_due or 0}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@billing_bp.route('/billing-data', methods=['GET'])
def billing_data():
    try:
        # Query all billing records
        bills = Billing.query.all()

        # Prepare the data as a list of dictionaries
        billing_list = []
        for bill in bills:
            product = Stock.query.filter_by(product_code=bill.product_code).first()
            product_name = product.item_name if product else "Unknown Product"
            billing_list.append({
                'bill_id': bill.bill_id,
                'customer_name': bill.customer_name,
                'customer_mobile': bill.customer_mobile,
                'product_code': bill.product_code,
                'product_name': product_name,
                'quantity': bill.quantity,
                'total_price': bill.total_price,
                'total_profit': bill.total_profit,
                'status': bill.status,
                'timestamp': bill.timestamp
            })

        return jsonify(billing_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500