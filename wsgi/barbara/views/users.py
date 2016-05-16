from flask import render_template, redirect, session, url_for, request, jsonify

from barbara import app, db

from barbara.models.users import User
from oxford.speaker_recognition.Identification import CreateProfile

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
    _speaker_profile_id = request.form['speakerProfileId']
    _wallet = 10000
    _currency_type = 'INR'
    new_user = User(first_name=_first_name, last_name=_last_name,
                    username=_username, password=_password, wallet=_wallet, currency_type=_currency_type,
                    speaker_profile_id=_speaker_profile_id)
    db.session.add(new_user)
    db.session.commit()
    return jsonify(success=True, result=new_user.to_dict())


@app.route("/api/login", methods=['POST'])
def login():
    _username = request.form['username']
    _password = request.form['password']
    user = User.query.filter_by(username=_username).first()
    if user and user.check_password(_password):
        return jsonify(success=True, item=user.to_dict())
    else:
        return jsonify(success=False, error='Invalid user credentials!!')
