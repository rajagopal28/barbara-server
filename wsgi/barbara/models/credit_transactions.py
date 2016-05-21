from barbara import db
from sqlalchemy.orm import relationship
import datetime


class CreditTransaction(db.Model):
    __tablename__ = 'credit_transactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    description = db.Column(db.String(128))
    amount = db.Column(db.Float)
    created_ts = db.Column(db.DateTime, default=datetime.datetime.now())
    last_updated_ts = db.Column(db.DateTime, default=datetime.datetime.now())
    user = relationship('User', foreign_keys=[user_id])

    def __init__(self, user_id,  description, amount):
        self.user_id = user_id
        self.amount = amount
        self.description = description

    def to_dict(self):
        return {
            'id': self.id,
            'userId': self.user_id,
            'amount': self.amount,
            'description': self.description,
            'user': self.user,
            'createdTS': self.created_ts,
            'lastUpdatedTS': self.last_updated_ts
        }