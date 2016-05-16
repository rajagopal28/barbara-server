from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
# Include config from config.py
app.config.from_pyfile('config.py')

# Create an instance of SQLAclhemy
db = SQLAlchemy(app)


import barbara.views.users
import barbara.views.transactions

if __name__ == "__main__":
    app.run()
