from flask import render_template, session, request, jsonify
from barbara import app, db

from barbara.models.users import User
from barbara.models.transactions import Transaction
from barbara.models.credit_transactions import CreditTransaction
from barbara.helpers.command_processor import process_command, find_substring


@app.route("/from-transactions", methods=['GET'])
def from_user_transactions():
    if session['user']:
        _user_id = session['user']['id']
        _user_transactions = Transaction.query.filter_by(to_user_id=_user_id).order_by(
                Transaction.created_ts.desc()).all()
        return render_template('user-transactions.html', user_transactions=_user_transactions)


@app.route("/to-transactions", methods=['GET'])
def to_user_transactions():
    if session['user']:
        _user_id = session['user']['id']
        _user_transactions = Transaction.query.filter_by(from_user_id=_user_id).order_by(
                Transaction.created_ts.desc()).all()
        return render_template('user-transactions.html', user_transactions=_user_transactions)


@app.route("/process-command", methods=['GET', 'POST'])
def process_user_command():
    _command_response = None
    if session['user']:
        _user_id = session['user']['id']
        if request.method == 'POST':
            _input_command = request.form['command']
            _command_response = process_command(_input_command)
            print _command_response.to_dict()
            _command_response = process_command_response(_command_response, _user_id)
        return render_template('chat-bot.html', command_response=_command_response)


def process_command_response(command_response, user_id):
    if command_response.is_reminder_request:
        # do nothing
        pass
    elif command_response.is_schedule_request:
        if command_response.referred_amount and command_response.referred_user != 'self':
            # do nothing
            pass
    elif command_response.is_read_request:
        if command_response.is_credit_account and command_response.is_current_balance_request:
            _user = User.query.filter_by(id=user_id).first()
            command_response.response_text = 'Your credit card outstanding is ' + _user.currency_type + ' ' + _user.credit
        elif command_response.is_current_balance_request:
            _user = User.query.filter_by(id=user_id).first()
            command_response.response_text = 'Your account balance is ' + _user.currency_type + ' ' + _user.wallet
        elif command_response.is_read_sent_transaction:
            _transfers = Transaction.query.filter_by(from_user_id=user_id).order_by(Transaction.created_ts.desc()).all()
            _transfers = [transfer for transfer in _transfers if
                          transfer.to_user.first_name == command_response.referred_user or transfer.to_user.last_name == command_response.referred_user]
            if len(_transfers) > 0:
                command_response.response_text = 'Yeah, You have transferred ' + _transfers[0].amount \
                                                 + ' to ' + _transfers[0].to_user.full_name() \
                                                 + ' on ' + str(_transfers[0].created_ts)
            else:
                command_response.response_text = 'No such transaction!'

        elif command_response.referred_user != 'self':
            _transfers = Transaction.query.filter_by(to_user_id=user_id).order_by(Transaction.created_ts.desc()).all()
            _transfers = [transfer for transfer in _transfers if
                          transfer.from_user.first_name == command_response.referred_user or transfer.from_user.last_name == command_response.referred_user]
            if len(_transfers) > 0:
                command_response.response_text = 'Yeah, You received ' + _transfers[0].amount \
                                                 + ' from ' + _transfers[0].to_user.full_name() \
                                                 + ' on ' + str(_transfers[0].created_ts)
            else:
                command_response.response_text = 'No such transaction!'

    elif command_response.is_transaction_request:
        if command_response.is_credit_account:
            pay_credit_card_bill(user_id)
            command_response.response_text = 'Done paying your credit card outstanding'
        else:
            transfer_amount_to_user(user_id, command_response.referred_user, command_response.referred_amount)
            command_response.response_text = 'Done transferring ' + command_response.referred_amount + ' to ' \
                                             + command_response.referred_user + ' now'
    return command_response


def pay_credit_card_bill(user_id):
    _user = User.query.filter_by(id=user_id).first()
    _user.wallet -= _user.credit
    credit_transaction = CreditTransaction(user_id=_user.id, description=' Payment. Thank you!!', amount=_user.credit)
    _user.credit = 0
    # create credit transaction
    db.session.add(credit_transaction)
    db.session.commit()


def transfer_amount_to_user(current_user_id, referred_user, referred_amount):
    _to_user = User.query.filter((User.first_name.ilike(referred_user)) | (
        User.last_name.ilike(referred_user))).first()
    _current_user = User.query.filter_by(id=current_user_id).first()
    _to_user.wallet += float(referred_amount)
    _current_user.wallet -= float(referred_amount)
    _transaction = Transaction(from_user_id=current_user_id, to_user_id=_to_user.id,
                               description='Transferring -' + referred_amount + '- to ' + referred_user,
                               amount=float(referred_amount))
    db.session.add(_transaction)
    # create transaction
    db.session.commit()
