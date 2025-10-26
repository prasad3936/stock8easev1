# services/account_service.py

from flask import Blueprint, render_template, request,url_for, redirect
from extensions import db

account_bp = Blueprint('account', __name__)

# services/account_service.py
from extensions import db

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(120), nullable=False, unique=True)
    firm_name = db.Column(db.String(120), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    mobile = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(120), nullable=False)
    

    def __init__(self, user_name, email,mobile, password, firm_name):
        self.user_name = user_name
        self.firm_name = firm_name
        self.email = email
        self.mobile = mobile
        self.password = password
        

@account_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    user = Account.query.first()
    if not user:
        return "No user found. Please create an account first.", 404
    render_template('account.html')

    if request.method == 'POST':
        user.user_name = request.form['username']
        user.email = request.form['email']
        user.mobile = request.form['mobile']
        user.firm_name = request.form['firm_name']
        db.session.commit()
        return "Profile updated successfully!", 200

    return render_template('account.html', user=user)

# User Profile Route
#@account_bp.route('/profile', methods=['GET', 'POST'])
#def profile():
#    user = Account.query.first()
#    if request.method == 'POST':
#        user.username = request.form['username']
#        user.email = request.form['email']
#        user.sales_target = float(request.form['sales_target'])
#        user.expenses = float(request.form['expenses'])
#        db.session.commit()

 #   return render_template('profile.html', user=user)

# Sales Target and Expenses
@account_bp.route('/target_and_expenses', methods=['GET', 'POST'])
def target_and_expenses():
    user = Account.query.first()
    if request.method == 'POST':
        user.sales_target = float(request.form['sales_target'])
        user.expenses = float(request.form['expenses'])
        db.session.commit()
    
    return render_template('target_and_expenses.html', user=user)

@account_bp.route('/account')
def account():
    user = Account.query.first()
    if not user:
        # Redirect to the create_account.html page
        return redirect(url_for('account.add_user'))

    return render_template('account.html', user=user)



@account_bp.route('/add', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        user_name = request.form.get('username')
        email = request.form.get('email')
        mobile = request.form.get('mobile')
        password = request.form.get('password')
        firm_name = request.form.get('firm_name')

        new_user = Account(
            user_name=user_name,
            email=email,
            mobile=mobile,
            password=password,
            firm_name=firm_name
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('account.account')) 

    return render_template('create_account.html')

@account_bp.route('/create_account')
def create_account():
    return render_template('create_account.html')

# Edit User Profile Route
@account_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_account(id):
    user = Account.query.get_or_404(id)
    
    if request.method == 'POST':
        user.user_name = request.form['username']
        user.email = request.form['email']
        user.mobile = request.form['mobile']
        user.firm_name = request.form['firm_name']
        
        # Commit changes to the database
        db.session.commit()
        
        #flash('Profile updated successfully!', 'success')
        return redirect(url_for('account.profile'))

    return render_template('edit_account.html', user=user)

# Delete User Account Route
@account_bp.route('/delete/<int:id>', methods=['POST'])
def delete_account(id):
    user = Account.query.get_or_404(id)
    
    # Delete the user from the database
    db.session.delete(user)
    db.session.commit()
    
    #flash('Account deleted successfully!', 'danger')
    return redirect(url_for('account.create_account'))