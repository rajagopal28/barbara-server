from barbara import db
import datetime
from sqlalchemy.orm import relationship
from werkzeug import generate_password_hash, check_password_hash


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(128))
    last_name = db.Column(db.String(128))
    username = db.Column(db.String(128))
    password = db.Column(db.String(128))
    currency_type = db.Column(db.String(128))
    wallet = db.Column(db.Float)
    speaker_profile_id = db.Column(db.String(128))
    created_ts = db.Column(db.DateTime, default=datetime.datetime.now())
    last_updated_ts = db.Column(db.DateTime, default=datetime.datetime.now())

    def __init__(self, first_name, last_name, username, password, currency_type, wallet, speaker_profile_id):
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.password = generate_password_hash(password)
        self.currency_type = currency_type
        self.wallet = wallet
        self.speaker_profile_id = speaker_profile_id

    def check_password(self, _password):
        return check_password_hash(self.password, _password)

    def full_name(self):
        return self.first_name + ' ' + self.last_name

    def to_dict(self):
        return {
            'id': self.id,
            'firstName': self.first_name,
            'lastName': self.last_name,
            'fullName': self.full_name(),
            'username': self.username,
            'speakerProfileId': self.speaker_profile_id,
            'currencyType': self.currency_type,
            'wallet': self.wallet,
            'createdTS': self.created_ts,
            'lastUpdatedTS': self.last_updated_ts,
        }
