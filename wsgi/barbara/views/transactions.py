from flask import render_template, session, request, jsonify
from sqlalchemy.sql import text

from barbara import app, db

from barbara.models.users import User
from barbara.models.transactions import Transaction


@app.route("/my-transactions/<user_id>", methods=['GET', 'POST'])
def user_transactions(user_id=None):
    _user_transactions = Transaction.query.filter_by(from_user_id=user_id).order_by(Transaction.created_ts.desc()).all()
    return render_template('user-transactions.html', user_transactions=_user_transactions)
