from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    id_number = db.Column(db.String(50), unique=True, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    loans = db.relationship('Loan', backref='user', lazy=True)

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    loan_amount = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='active')  # Add status field

    repayments = db.relationship('Repayment', backref='loan', lazy=True)

    def is_loan_completed(self):
        # Calculate the current date
        current_date = datetime.today().date()
        # Calculate the 13th day from the start date
        end_date = self.start_date + timedelta(days=13)
        # Check if the current date is after the 13th day
        if current_date > end_date:
            self.status = 'completed'
            db.session.commit()
            return True
        else:
            return False

    def get_daily_repayment_amount(self):
        # Ensure the loan is active
        if self.status != 'active':
            return 0
        # Calculate the daily repayment amount
        daily_repayment_amount = self.loan_amount / 10
        return daily_repayment_amount

    def get_current_repayment_day(self):
        # Calculate the current date
        current_date = datetime.today().date()
        # Calculate the start date plus one day (day 1)
        repayment_start_date = self.start_date + timedelta(days=1)
        # Calculate the current repayment day
        repayment_day = (current_date - repayment_start_date).days + 1

        return max(0, repayment_day)  # Ensure repayment_day is non-negative


class Repayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loan.id'), nullable=False)
    repayment_amount = db.Column(db.Float, nullable=False)
    repayment_date = db.Column(db.Date, nullable=False)
