from flask import render_template, redirect, session, url_for, request, jsonify
from werkzeug import secure_filename
from os import path, remove

from barbara import app, db

from barbara.models.users import User
from barbara.models.user_preferences import UserPreference
from barbara.models.invetment_plans import InvestmentPlan


from oxford.speaker_recognition.Verification.CreateProfile import create_profile
from oxford.speaker_recognition.Verification.EnrollProfile import enroll_profile
from oxford.speaker_recognition.Verification.VerifyFile import verify_file


@app.route("/users")
def view_users():
    all_users = User.query.order_by(User.first_name.asc()).all()
    return render_template('users.html', users=all_users)


@app.route("/login", methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        _username = request.form['username']
        _password = request.form['password']
        user = User.query.filter_by(username=_username).first()
        if user and user.check_password(_password):
            session['user'] = user.to_dict()
            return redirect(url_for('home'))
        else:
            return render_template("login-form.html", error='Invalid user credentials!!')
    else:
        return render_template("login-form.html")


@app.route("/logout")
def logout_user():
    if session.get('user', None):
        session.clear()
    return redirect(url_for('home'))


@app.route("/enroll-voice", methods=['POST', 'GET'])
def voice_register():
    # print_all_profiles(app.config['MICROSOFT_SPEAKER_RECOGNITION_KEY'])
    if request.method == 'POST':
        # receive voice file from request
        _user_id = request.form['userId']
        user = User.query.filter_by(id=_user_id).first()
        _file = request.files['file']
        if _file and user:
            filename = secure_filename(_file.filename)
            # print app.config['UPLOAD_FOLDER']
            _created_file_path = path.join(app.config['UPLOAD_FOLDER'], filename)
            _file.save(_created_file_path)
            print app.config['MICROSOFT_SPEAKER_RECOGNITION_KEY']
            print user.speaker_profile_id
            print _created_file_path
            enroll_profile(app.config['MICROSOFT_SPEAKER_RECOGNITION_KEY'], user.speaker_profile_id, _created_file_path)
        # register with the current user's speaker profile
        return redirect(url_for('home'))
    else:
        return render_template('post-voice.html')


@app.route("/verify-voice", methods=['POST', 'GET'])
def voice_enrollment():
    # print_all_profiles(app.config['MICROSOFT_SPEAKER_RECOGNITION_KEY'])
    if request.method == 'POST':
        # receive voice file from request
        _user_id = request.form['userId']
        user = User.query.filter_by(id=_user_id).first()
        _file = request.files['file']
        if _file and user:
            filename = secure_filename(_file.filename)
            # print app.config['UPLOAD_FOLDER']
            _created_file_path = path.join(app.config['UPLOAD_FOLDER'], filename)
            _file.save(_created_file_path)
            print app.config['MICROSOFT_SPEAKER_RECOGNITION_KEY']
            print user.speaker_profile_id
            print _created_file_path
            verification_response = verify_file(app.config['MICROSOFT_SPEAKER_RECOGNITION_KEY'], _created_file_path,
                                                user.speaker_profile_id)
            remove(_created_file_path)
        # register with the current user's speaker profile
        return redirect(url_for('home'))
    else:
        return render_template('post-voice.html')


@app.route("/my-profile")
def my_profile():
    if session.get('user', None):
        _user_info = User.query.filter_by(id=session['user']['id']).first()
        return render_template('my-profile.html', user=_user_info)
    return 'Not logged In', 401


@app.route("/api/users/all")
def get_users():
    all_users = User.query.order_by(User.first_name.asc()).all()
    result = [user.to_dict() for user in all_users]
    return jsonify(items=result, success=True)


@app.route("/api/users/add", methods=['POST'])
def add_user():
    _first_name = request.form['firstName']
    _last_name = request.form['lastName']
    _username = request.form['username']
    _password = request.form['password']
    _speaker_profile_id = create_profile(app.config['MICROSOFT_SPEAKER_RECOGNITION_KEY'], app.config['DEFAULT_LOCALE'])
    # request.form['speakerProfileId']
    _wallet = 10000
    _credit = 0
    _currency_type = 'INR'
    new_user = User(first_name=_first_name, last_name=_last_name,
                    username=_username, password=_password, wallet=_wallet,
                    credit=_credit, currency_type=_currency_type,
                    speaker_profile_id=_speaker_profile_id)
    db.session.add(new_user)
    db.session.commit()
    return jsonify(success=True, item=new_user.to_dict())


@app.route("/api/users/save-preferences", methods=['POST'])
def save_user_preferences():
    _user_id = request.form['userId']
    _budget = request.form['budget']
    _security_question = request.form['securityQuestion']
    _nick_name = request.form['nickName']
    if _user_id:
        user_preference = UserPreference.query.filter_by(user_id=_user_id).first()
        if not user_preference:
            user_preference = UserPreference(user_id=_user_id)
            db.session.add(user_preference)
        if _budget:
            user_preference.budget = float(_budget)
        if _nick_name:
            user_preference.nick_name = _nick_name
        if _security_question:
            user_preference.security_question = _security_question
        db.session.commit()
        return jsonify(success=True, item=user_preference.to_dict())
    return jsonify(success=False, item=None)


@app.route("/api/users/preferences", methods=['GET'])
def get_user_preferences():
    _user_id = request.args['userId']
    if _user_id:
        user_preference = UserPreference.query.filter_by(user_id=_user_id).first()
        return jsonify(success=True, item=user_preference.to_dict())
    return jsonify(success=False, item=None)


@app.route("/api/login", methods=['POST'])
def login():
    _username = request.form['username']
    _password = request.form['password']
    user = User.query.filter_by(username=_username).first()
    if user and user.check_password(_password):
        return jsonify(success=True, item=user.to_dict())
    else:
        return jsonify(success=False, error='Invalid user credentials!!')


@app.route("/investment-plans", methods=['GET'])
def investment_plans():
    _plans = InvestmentPlan.query.all()
    return render_template('investment-plans.html', plans=_plans)
