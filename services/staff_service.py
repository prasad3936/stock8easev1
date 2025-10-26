from flask import Flask, Blueprint, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from extensions import db

# Define the blueprint
staff_bp = Blueprint('staff', __name__)

# Define models
class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    mobile = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    salary = db.Column(db.Float, nullable=False)
    attendance = db.relationship('Attendance', backref='staff', lazy=True)


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)  # One record per day per staff
    punch_in = db.Column(db.DateTime, nullable=False)
    punch_out = db.Column(db.DateTime, nullable=True)
    working_hours = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='Absent')


class SalarySlip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    month = db.Column(db.String(7), nullable=False)  # Format: YYYY-MM
    year = db.Column(db.Integer, nullable=False)
    full_days = db.Column(db.Integer, nullable=False)
    half_days = db.Column(db.Integer, nullable=False)
    total_payment = db.Column(db.Float, nullable=False)

# Routes

# Add Staff
@staff_bp.route('/add', methods=['GET', 'POST'])
def add_staff():
    if request.method == 'POST':
        name = request.form['name']
        mobile = request.form['mobile']
        email = request.form['email']
        salary = request.form['salary']
        new_staff = Staff(name=name, mobile=mobile, email=email, salary=float(salary))
        db.session.add(new_staff)
        db.session.commit()
        return redirect(url_for('staff.staff_list'))
    return render_template('add_staff.html')

@staff_bp.route('/')
def staff_list():
    staff = Staff.query.all()
    today = date.today()

    # Loop through each staff and check their attendance for today
    for member in staff:
        attendance = Attendance.query.filter_by(staff_id=member.id, date=today).first()
        # If attendance exists, set whether they've punched in
        member.today_punched_in = attendance is not None and attendance.punch_in is not None
        member.today_punched_out = attendance is not None and attendance.punch_out is not None

    current_month = today.strftime('%Y-%m')
    return render_template('staff_list.html', staff=staff, current_month=current_month)

# Punch In
@staff_bp.route('/punch_in/<int:staff_id>', methods=['POST'])
def punch_in(staff_id):
    today = datetime.today().date()

    # Check if the staff has already punched in for today
    existing_attendance = Attendance.query.filter_by(staff_id=staff_id, date=today).first()
    if not existing_attendance:
        new_attendance = Attendance(staff_id=staff_id, date=today, punch_in=datetime.now(), status='Absent')
        db.session.add(new_attendance)
        db.session.commit()
    
    return redirect(url_for('staff.staff_list'))

# Punch Out
@staff_bp.route('/punch_out/<int:staff_id>', methods=['POST'])
def punch_out(staff_id):
    today = datetime.today().date()
    attendance = Attendance.query.filter_by(staff_id=staff_id, date=today).first()

    if attendance and not attendance.punch_out:  # If the user has punched in but not out
        # Update punch_out time and calculate working hours
        attendance.punch_out = datetime.now()
        delta = attendance.punch_out - attendance.punch_in
        attendance.working_hours = round(delta.total_seconds() / 3600, 2)

        # Determine status based on working hours
        if attendance.working_hours >= 5:
            attendance.status = 'Full Day'
        elif attendance.working_hours >= 3:
            attendance.status = 'Half Day'
        else:
            attendance.status = 'Absent'
        
        db.session.commit()

    # After punching out, the user cannot punch in or out again for the day
    # This will return to the staff list with the updated status
    return redirect(url_for('staff.staff_list'))


# Generate Payroll
@staff_bp.route('/generate_payroll/<int:staff_id>', methods=['GET'])
def generate_payroll(staff_id):
    month = request.args.get('month', default=datetime.today().strftime('%Y-%m'))
    staff = Staff.query.get_or_404(staff_id)
    attendances = Attendance.query.filter(
        Attendance.staff_id == staff_id,
        Attendance.date.like(f"{month}-%")
    ).all()
    
    full_days = sum(1 for a in attendances if a.status == 'Full Day')
    half_days = sum(1 for a in attendances if a.status == 'Half Day')
    per_day_rate = staff.salary / 30
    total_payment = full_days * per_day_rate + half_days * (per_day_rate / 2)
    
    salary_slip = SalarySlip(
        staff_id=staff_id, 
        month=month, 
        year=int(month.split('-')[0]), 
        full_days=full_days, 
        half_days=half_days, 
        total_payment=total_payment
    )
    db.session.add(salary_slip)
    db.session.commit()
    
    return render_template('payroll.html', staff=staff, month=month, full_days=full_days, half_days=half_days, total_payment=total_payment)
