from flask import Flask
from flask import render_template, request, redirect, url_for
from models import db, User, Loan, Repayment
from sqlalchemy import or_
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///loan_management.db'
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    loans = Loan.query.all()
    users = User.query.all()
    total_users = len(users)

    # 2. Total Amount of Loans
    total_loans_amount = sum(loan.loan_amount for loan in loans)

    # 3. Todays Repayments Expected (for Active Loans)
    todays_repayments_expected = sum(loan.get_daily_repayment_amount() for loan in loans if loan.status == 'active' and loan.get_current_repayment_day() > 0)
    # Calculate daily repayment amount and repayment cycle for each loan
    for loan in loans:
        # Calculate the number of days between the start date and today
        days_since_start = (datetime.now().date() - loan.start_date).days

        # Exclude day 0 from the count
        repayment_days = max(0, days_since_start)

        # Calculate daily repayment amount
        daily_repayment_amount = loan.loan_amount / 10
        current_repayment_day = loan.get_current_repayment_day()
        repayment_cycle = f"Day {current_repayment_day}"

        # Determine repayment cycle
        # Update loan object with calculated values
        loan.daily_repayment_amount = daily_repayment_amount
        loan.repayment_cycle = repayment_cycle

    return render_template('home.html', loans=loans, users=users, total_users=total_users, total_loans_amount=total_loans_amount, todays_repayments_expected=todays_repayments_expected)

@app.route('/customers')
def customers():
    search_query = request.args.get('q', '')
    if search_query:
        users = User.query.filter(or_(User.name.startswith(search_query), User.id_number.startswith(search_query))).all()
    else:
        users = User.query.all()

    return render_template('users.html', users=users)

@app.route('/user/<int:user_id>')
def user_details(user_id):
    # Connect to SQLite database
    conn = sqlite3.connect('instance/loan_management.db')
    cursor = conn.cursor()

    # Fetch user details from the database
    cursor.execute("SELECT * FROM user WHERE id=?", (user_id,))
    user = cursor.fetchone()

    # Fetch the active loan amount for the user
    cursor.execute("SELECT loan_amount FROM loan WHERE user_id=? AND status='active'", (user_id,))
    active_loan_amount = cursor.fetchone()
    active_loan_amount = active_loan_amount[0] if active_loan_amount else None
    # Close database connection
    conn.close()

        # Fetch all loans for the user
    user_loans = Loan.query.filter_by(user_id=user_id).all()
    # Initialize variables to store loan details
    active_loan_amount = None
    current_repayment_day = None
    daily_repayment_amount = None
    loan_statuses = []

    # Check if the user has an active loan
    active_loan = next((loan for loan in user_loans if loan.status == 'active'), None)
    if active_loan:
        active_loan_amount = active_loan.loan_amount
        current_repayment_day = active_loan.get_current_repayment_day()
        daily_repayment_amount = active_loan.get_daily_repayment_amount()

    # Retrieve statuses of all loans
    for loan in user_loans:
        loan_statuses.append({'loan_amount': loan.loan_amount,'loan_id': loan.id, 'status': loan.status})

    # Render the HTML template with user details and active loan amount
    return render_template('single_user.html',
                           name=user[1],
                           phone_number=user[2],
                           location=user[3],
                           id_number=user[4],
                           active_loan_amount=active_loan_amount,
                           user_id=user_id,
                           current_repayment_day=current_repayment_day,
                           daily_repayment_amount=daily_repayment_amount,
                           loan_statuses=loan_statuses)

@app.route('/new_user', methods=['POST'])
def create_user():
    name = request.form.get('name')
    location = request.form.get('location')
    id_number = request.form.get('id_number')
    phone_number = request.form.get('phone_number')

    new_user = User(name=name, location=location, id_number=id_number, phone_number=phone_number)
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('customers'))


@app.route('/new_loan', methods=['POST'])
def issue_loan():
    if request.method == 'POST':
        # Get data from the form
        loan_amount = request.form.get('amount')
        user_id = request.form.get('userId')
        start_date = request.form.get('start_date') or datetime.now().date()

        # Create a new loan object
        new_loan = Loan(user_id=user_id, loan_amount=loan_amount, start_date=datetime.today())

        # Add the new loan to the database
        db.session.add(new_loan)
        db.session.commit()

        return redirect(url_for('customers'))



if __name__ == '__main__':
    app.run(debug=True)
