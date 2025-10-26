from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from datetime import datetime
from extensions import db

stock_bp = Blueprint('stock', __name__)

class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Adding an ID column as the primary key
    product_code = db.Column(db.String(50), unique=True, nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    expiry = db.Column(db.String(10), nullable=False)  # Keep as string
    quantity = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        """Convert stock to a dictionary with formatted expiry date."""
        expiry_date = datetime.strptime(self.expiry, '%Y-%m-%d')
        return {
            'product_code': self.product_code,
            'item_name': self.item_name,
            'selling_price': self.selling_price,
            'price': self.price,
            'expiry': expiry_date.strftime('%Y-%m-%d'),  # Format as string
            'quantity': self.quantity
        }

    def __repr__(self):
        return f'<Stock {self.product_code} - {self.item_name}>'

# Utility function to generate product code based on item name
def generate_product_code(item_name):
    """Generate a unique product code based on item name."""
    return item_name[:3].upper() + str(db.session.query(Stock).count() + 1)

from datetime import datetime, timedelta

def get_near_to_expiry_stock(days=30):
    """Fetch stock items expiring within the given number of days."""
    today = datetime.today()
    threshold_date = today + timedelta(days=days)
    return Stock.query.filter(
        datetime.strptime(Stock.expiry, '%Y-%m-%d') <= threshold_date
    ).all()

@stock_bp.route('/overview', methods=['GET'])
def stock_overview():
    """Route to display stock overview."""
    try:
        # Count unique stock items
        total_items = Stock.query.count()

        # Get near-to-expiry items
        near_to_expiry_items = get_near_to_expiry_stock(days=30)

        return jsonify({
            'total_items': total_items,
            'near_to_expiry_count': len(near_to_expiry_items),
            'near_to_expiry_items': [item.to_dict() for item in near_to_expiry_items]
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route to add stock
@stock_bp.route('/add', methods=['GET', 'POST'])
def add_stock():
    """Route for adding stock items."""
    if request.method == 'POST':
        item_name = request.form['item_name']
        selling_price = float(request.form['selling_price'])
        price = float(request.form['price'])
        expiry = request.form['expiry']
        quantity = int(request.form['quantity'])

        product_code = generate_product_code(item_name)

        new_stock = Stock(
            product_code=product_code,
            item_name=item_name,
            selling_price=selling_price,
            price=price,
            expiry=expiry,
            quantity=quantity
        )

        db.session.add(new_stock)
        db.session.commit()

        return redirect(url_for('stock.view_stock'))

    return render_template('add_stock.html')

# Route to view all stock
@stock_bp.route('/view')
def view_stock():
    """Route to display all stock items."""
    stocks = Stock.query.all()
    return render_template('view_stock.html', stocks=stocks)

# Route to decrease quantity based on sales
@stock_bp.route('/sell/<product_code>', methods=['POST'])
def sell_product(product_code):
    """Route to handle selling of stock items."""
    stock_item = Stock.query.filter_by(product_code=product_code).first()
    if stock_item:
        quantity_sold = int(request.form['quantity_sold'])
        if stock_item.quantity >= quantity_sold:
            stock_item.quantity -= quantity_sold
            db.session.commit()
            return redirect(url_for('stock.view_stock'))
        return 'Not enough stock available', 400  # Handle insufficient stock
    return 'Product not found', 404

# Test route to check all stock items in JSON format
@stock_bp.route('/test-stock', methods=['GET'])
def test_stock():
    """Test route for returning stock items as JSON."""
    try:
        stocks = db.session.query(Stock).all()
        return jsonify([stock.to_dict() for stock in stocks]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Another test route for viewing all stock items in JSON format
@stock_bp.route('/stock', methods=['GET'])
def view():
    """Test route for returning all stock items in JSON format."""
    try:
        stocks = db.session.query(Stock).all()
        return jsonify([stock.to_dict() for stock in stocks]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@stock_bp.route('/expired-items', methods=['GET'])
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
    
@stock_bp.route('/edit/<product_code>', methods=['GET', 'POST'])
def edit_stock(product_code):
    """Route to edit stock items using product_code."""
    stock_item = Stock.query.filter_by(product_code=product_code).first()

    if not stock_item:
        return "Product not found", 404

    if request.method == 'POST':
        # Update stock item with data from the form
        stock_item.item_name = request.form['item_name']
        stock_item.selling_price = float(request.form['selling_price'])
        stock_item.price = float(request.form['price'])
        stock_item.expiry = request.form['expiry']
        stock_item.quantity = int(request.form['quantity'])

        db.session.commit()
        return redirect(url_for('stock.view_stock'))

    # Render the edit form with the current stock details
    return render_template('edit_stock.html', stock=stock_item)

@stock_bp.route("/delete-stock/<product_code>", methods=["GET"])
def delete_stock(product_code):
    try:
        # Query the stock item by its product code
        stock_item = Stock.query.filter_by(product_code=product_code).first()

        # If the stock item doesn't exist, flash an error message and redirect
        if not stock_item:
            flash("Stock item not found.", "danger")
            return redirect(url_for("view_stock"))

        # Delete the stock item from the database
        db.session.delete(stock_item)
        db.session.commit()

        # Flash a success message
        flash("Stock item successfully deleted.", "success")
    except Exception as e:
        # Handle any exceptions and flash an error message
        db.session.rollback()
        flash(f"An error occurred while deleting the stock item: {str(e)}", "danger")

    # Redirect to the stock overview page
    return redirect(url_for("view_stock"))