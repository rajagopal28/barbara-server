from flask import render_template

from barbara import app, db


@app.route("/")
def home():
    return render_template('home.html')


@app.route("/about-app")
def about_app():
    return render_template('about-app.html')
