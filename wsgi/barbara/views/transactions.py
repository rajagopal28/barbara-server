from flask import render_template, session, request, jsonify, redirect, url_for
import datetime
from werkzeug import secure_filename
from os import remove, path
from barbara import app, db

from barbara.models.users import User
from barbara.models.user_preferences import UserPreference
from barbara.models.transactions import Transaction
from barbara.models.command_response import CommandResponse
from barbara.models.credit_transactions import CreditTransaction
from barbara.models.investment_plans import InvestmentPlan
from barbara.helpers.command_processor import process_command, get_mis_replies
from barbara.helpers.mail_processor import read_email

from oxford.speaker_recognition.Verification.VerifyFile import verify_file

VERIFICATION_RESULT_ACCEPT = 'Accept'
VERIFICATION_CONFIDENCE = ['Low', 'Normal', 'High']


@app.route("/transactions", methods=['GET'])
def to_user_transactions():
    if session['user']:
        _user_id = session['user']['id']
        _user_transactions = Transaction.query.filter(
                (Transaction.from_user_id == _user_id) | (Transaction.to_user_id == _user_id)).order_by(
                Transaction.created_ts.desc()).all()
        return render_template('user-transactions.html', user_transactions=_user_transactions)


@app.route("/credit-transactions", methods=['GET'])
def credit_transactions():
    if session['user']:
        _user_id = session['user']['id']
        _user_transactions = CreditTransaction.query.filter_by(user_id=_user_id).order_by(
                CreditTransaction.created_ts.desc()).all()
        return render_template('user-credit-transactions.html', user_transactions=_user_transactions)


@app.route("/credit-transactions/shop", methods=['GET', 'POST'])
def shop_credit_transactions():
    if request.method == 'POST':
        if session['user']:
            _user_id = session['user']['id']
            _description = request.form['description']
            _amount = request.form['amount']
            new_credit_transaction = CreditTransaction(user_id=_user_id, description=_description, amount=_amount)
            user = User.query.filter_by(id=_user_id).first()
            user.credit += float(_amount)
            db.session.add(new_credit_transaction)
            db.session.commit()
        return redirect(url_for('credit_transactions'))
    return render_template('shop-credit-transaction.html')


@app.route("/api/transactions/all")
def get_user_to_transactions():
    _user_id = request.args['userId']
    _user_transactions = Transaction.query.filter(
            (Transaction.from_user_id == _user_id) | (Transaction.to_user_id == _user_id)).order_by(
            Transaction.created_ts.desc()).all()
    result = [transaction.to_dict() for transaction in _user_transactions]
    return jsonify(items=result, success=True)


@app.route("/api/transactions/credit/all")
def get_user_credit_transactions():
    _user_id = request.args['userId']
    _user_transactions = CreditTransaction.query.filter_by(user_id=_user_id).order_by(
            CreditTransaction.created_ts.desc()).all()
    result = [transaction.to_dict() for transaction in _user_transactions]
    return jsonify(items=result, success=True)


@app.route("/api/command/process", methods=['POST'])
def process_app_user_command():
    _user_id = request.form['userId']
    _input_command = request.form['command']
    _command_response = process_command(_input_command)
    _command_response.user_id = _user_id
    _command_response = process_command_response(_command_response, _user_id)
    result = _command_response.to_dict()
    return jsonify(item=result, success=True)


@app.route("/process-command", methods=['GET', 'POST'])
def process_user_command():
    if session['user']:
        _user_id = session['user']['id']
        _command_history = []
        _command_start_id = None
        _command_response = None
        if request.method == 'POST':
            _input_command = request.form['command']
            print _input_command
            _command_start_id = request.form['startCommandId']
            _command_response = process_command(command_sentence=_input_command)
            _command_response.user_id = _user_id
            print _command_response.to_dict()
            _command_response = process_command_response(command_response=_command_response, user_id=_user_id)
            db.session.add(_command_response)
            db.session.commit()
            if _command_start_id:
                _command_history = CommandResponse.query \
                    .filter_by(user_id=_user_id) \
                    .filter(CommandResponse.id > int(_command_start_id)) \
                    .order_by(CommandResponse.created_ts.asc()).all()
            else:
                _command_start_id = _command_response.id
            print _input_command
            _command_history.append(_command_response)
        return render_template('chat-bot.html', command_history=_command_history,
                               current_session_command_start=_command_start_id, command_response=_command_response)


@app.route("/api/transactions/authenticate-transfer", methods=['POST'])
def voice_verification():
    # receive voice file from request
    _user_id = request.form['userId']
    _command_sentence = request.form['command']
    user = User.query.filter_by(id=_user_id).first()
    _file = request.files['file']
    result = None
    user_verified = False
    if _file and user:
        filename = secure_filename(_file.filename)
        # print app.config['UPLOAD_FOLDER']
        _created_file_path = path.join(app.config['UPLOAD_FOLDER'], filename)
        _file.save(_created_file_path)
        # print app.config['MICROSOFT_SPEAKER_RECOGNITION_KEY']
        # print user.speaker_profile_id
        # print _created_file_path
        try:
            verification_response = verify_file(app.config['MICROSOFT_SPEAKER_RECOGNITION_KEY'], _created_file_path,
                                                user.speaker_profile_id)
            _index = VERIFICATION_CONFIDENCE.index(verification_response.get_confidence())
            user_verified = VERIFICATION_RESULT_ACCEPT == verification_response.get_result()
            user_verified = user_verified and (_index != -1)
        except Exception:
            user_verified = False
        remove(_created_file_path)
        if user_verified and _command_sentence:
            command_response = process_command(_command_sentence)
            command_response.user_id = _user_id
            if command_response.is_credit_account:
                pay_credit_card_bill(_user_id)
                command_response.response_text = 'Done paying your credit card outstanding'
            else:
                transfer_amount_to_user(_user_id, command_response.referred_user, command_response.referred_amount)
                command_response.response_text = 'Done transferring ' + command_response.referred_amount + ' to ' \
                                                 + command_response.referred_user
            # reset the authentication flags to avoid looping back
            command_response.is_transaction_request = False
            command_response.is_schedule_request = False
            command_response.is_reminder_request = False
            result = command_response.to_dict()
            # add the command to database
            db.session.add(command_response)
            db.session.commit()
    # register with the current user's speaker profile
    return jsonify(success=user_verified, item=result)


@app.route("/authenticate-transfer", methods=['POST'])
def authenticate_user_command():
    if session['user']:
        user_id = session['user']['id']
        is_credit_account = request.form['isCreditAccount']
        referred_user = request.form['referredUser']
        referred_amount = request.form['referredAmount']
        user = User.query.filter_by(id=user_id).first()
        _file = request.files['file']
        if _file and user and referred_user and referred_amount:
            filename = secure_filename(_file.filename)
            # print app.config['UPLOAD_FOLDER']
            _created_file_path = path.join(app.config['UPLOAD_FOLDER'], filename)
            _file.save(_created_file_path)
            # print app.config['MICROSOFT_SPEAKER_RECOGNITION_KEY']
            # print user.speaker_profile_id
            # print _created_file_path
            try:
                verification_response = verify_file(app.config['MICROSOFT_SPEAKER_RECOGNITION_KEY'], _created_file_path,
                                                    user.speaker_profile_id)
                _index = VERIFICATION_CONFIDENCE.index(verification_response.get_confidence())
                user_verified = VERIFICATION_RESULT_ACCEPT == verification_response.get_result()
                user_verified = user_verified and (_index != -1)
            except Exception:
                user_verified = False
            remove(_created_file_path)
            if user_verified:
                _command_sentence = 'Authenticating transfer...isCreditAccount=%s ; referredUser=%s; referredAmount=%s' % (
                    is_credit_account, referred_user, referred_amount)
                command_response = CommandResponse(input_command=_command_sentence)
                command_response.user_id = user_id
                if is_credit_account == 'true':
                    pay_credit_card_bill(user_id)
                    command_response.response_text = 'Done paying your credit card outstanding'
                else:
                    transfer_amount_to_user(user_id, referred_user, referred_amount)
                    command_response.response_text = 'Done transferring ' + referred_amount + ' to ' \
                                                     + referred_user + ' now'
                return render_template('chat-bot.html', command_response=command_response)


@app.route("/api/transactions/execute-verified-transfer", methods=['POST'])
def execute_verified_transfer():
    if request.form['userId']:
        user_id = request.form['userId']
        _command_sentence = request.form['command']
        command_response = process_command(_command_sentence)
        command_response.user_id = user_id
        if command_response.is_credit_account:
            pay_credit_card_bill(user_id)
            command_response.response_text = 'Done paying your credit card outstanding'
        else:
            transfer_amount_to_user(user_id, command_response.referred_user, command_response.referred_amount)
            command_response.response_text = 'Done transferring %s to %s now' % (command_response.referred_amount,
                                                                                 command_response.referred_user)
        _status = True
        # reset the authentication flags to avoid looping back
        command_response.is_transaction_request = False
        command_response.is_schedule_request = False
        command_response.is_reminder_request = False
        return jsonify(success=_status, item=command_response.to_dict())


def process_command_response(command_response, user_id):
    if command_response.is_reminder_request:
        command_response.scheduled_response_text = command_response.response_text
        command_response.response_text += ' added'
    elif command_response.is_promotions_check:
        print command_response.response_text
        if len(command_response.response_text) > 0:
            # check promotions mail
            promotions_key = command_response.response_text
            promotions_list = read_email(promotions_key)
            # get promotions from email
            command_response.response_text = 'Here are some matching promotions on %s' % promotions_key
            command_response.scheduled_response_text = ' %s' % promotions_list
    elif command_response.is_schedule_request or command_response.is_transaction_request:
        if command_response.is_transaction_request:
            # send a response so that the user inputs password
            _user_preference = UserPreference.query.filter_by(user_id=user_id).first()
            _command_suffix = 'Authenticate.'
            if _user_preference and _user_preference.security_question:
                _command_suffix = _user_preference.security_question
            command_response.response_text = 'Processing...' + _command_suffix
            if command_response.is_credit_account:
                command_response.scheduled_response_text = 'pay my credit card bill'
            elif command_response.referred_amount and command_response.referred_user and command_response.referred_user != 'self':
                command_response.scheduled_response_text = 'transfer ' + command_response.referred_amount + ' to ' \
                                                           + command_response.referred_user
    elif command_response.is_credit_account and command_response.is_current_balance_request:
        _user = User.query.filter_by(id=user_id).first()
        command_response.response_text = 'Your credit card outstanding is ' + _user.currency_type + ' ' + str(
                _user.credit)
    elif command_response.is_read_request or command_response.is_current_balance_request:
        if command_response.is_current_balance_request:
            _user = User.query.filter_by(id=user_id).first()
            command_response.response_text = 'Your account balance is ' + _user.currency_type + ' ' + str(_user.wallet)
        elif command_response.is_read_sent_transaction:
            _transfers = Transaction.query.filter_by(from_user_id=user_id) \
                .filter(Transaction.created_ts >= get_start_of_day(command_response.time_associated)) \
                .order_by(Transaction.created_ts.asc()).all()
            _transfers = [transfer for transfer in _transfers if
                          transfer.to_user.first_name.lower() == command_response.referred_user or transfer.to_user.last_name.lower() == command_response.referred_user]
            if len(_transfers) > 0:
                command_response.response_text = 'Yeah, You have transferred ' + str(_transfers[0].amount) \
                                                 + ' to ' + _transfers[0].to_user.full_name() \
                                                 + ' on ' + str(_transfers[0].created_ts)
            else:
                command_response.response_text = 'No such transaction!'

        elif command_response.referred_user != 'self':
            _transfers = Transaction.query.filter_by(to_user_id=user_id) \
                .filter(Transaction.created_ts >= get_start_of_day(command_response.time_associated)) \
                .order_by(Transaction.created_ts.asc()).all()
            _transfers = [transfer for transfer in _transfers if
                          transfer.from_user.first_name.lower() == command_response.referred_user or transfer.from_user.last_name.lower() == command_response.referred_user]
            if len(_transfers) > 0:
                command_response.response_text = 'Yeah. Got it.'
                command_response.scheduled_response_text = 'Yeah, You received ' + str(_transfers[0].amount) \
                                                           + ' from ' + _transfers[0].from_user.full_name() \
                                                           + ' on ' + str(_transfers[0].created_ts)
            else:
                command_response.response_text = 'No such transaction!'

    elif command_response.is_transaction_request:
        # send a response so that the user inputs password
        _user_preference = UserPreference.query.filter_by(user_id=user_id).first()
        _command_suffix = 'Authenticate.'
        if _user_preference and _user_preference.security_question:
            _command_suffix = _user_preference.security_question
        command_response.response_text = 'Processing...' + _command_suffix
        if command_response.is_credit_account:
            command_response.scheduled_response_text = 'pay my credit card bill'
        else:
            command_response.scheduled_response_text = 'transfer ' + command_response.referred_amount + ' to ' \
                                                       + command_response.referred_user
    elif command_response.is_budget_check:
        _user_preference = UserPreference.query.filter_by(user_id=user_id).first()
        if _user_preference is None:
            _user_preference = UserPreference(user_id=user_id)
            db.session.add(_user_preference)
            # create new and add if not present
        budget = _user_preference.budget
        if command_response.is_budget_change:
            # change the budget for this user
            new_budget = 0
            if command_response.response_text.isdigit():
                new_budget = float(command_response.response_text)
            command_response.response_text = 'Budget set to ' + str(new_budget)
            _user_preference.budget = new_budget
            db.session.commit()
        elif budget and budget > 0:
            # get the budget parameter from the request of whatever
            total_this_month_spend = total_spend_transactions(user_id)
            if budget >= total_this_month_spend:
                command_response.response_text = 'We are Cool on this month budget. Have fun.'
                # get investment plans here for the difference amount
                _investments = InvestmentPlan.query.filter(
                    InvestmentPlan.amount <= (budget - total_this_month_spend)).all()
                command_response.scheduled_response_text = 'Here are the list of investments you might like.\n'
                command_response.scheduled_response_text += '\n'.join([item.description for item in _investments])
            else:
                command_response.response_text = get_mis_replies()
                difference = total_this_month_spend - budget
                command_response.scheduled_response_text = 'We spent ' \
                                                           + str(difference) \
                                                           + ' more. Be cautious dude.'
        else:
            command_response.response_text = 'You\'ve not set any budget. What budget should I set?'
    if command_response.has_greeting_text:
        _user = User.query.filter_by(id=user_id).first()
        _user_preference = _user.preferences
        if _user_preference and _user_preference.nick_name:
            _nick_name = _user_preference.nick_name
        else:
            _nick_name = _user.full_name()
        command_response.response_text = 'Hey ' + _nick_name + '.' \
                                         + command_response.response_text
    return command_response


def total_spend_transactions(user_id):
    month_start = datetime.datetime.now()
    month_start = month_start - datetime.timedelta(days=month_start.day)
    _transactions = Transaction.query.filter_by(from_user_id=user_id).filter(Transaction.created_ts >= month_start)
    _user = User.query.filter_by(id=user_id).first()
    total_spend = _user.credit
    for transaction in _transactions:
        total_spend += transaction.amount
    return total_spend


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


def get_start_of_day(date_time_value):
    sod_time = datetime.time(0, 0, 0)
    return datetime.datetime.combine(date_time_value, sod_time)  # set time to end ot day i.e., 00:00:00
