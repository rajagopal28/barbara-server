from barbara import db
from sqlalchemy.orm import relationship
import datetime


class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(128))
    from_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    amount = db.Column(db.Float)
    created_ts = db.Column(db.DateTime, default=datetime.datetime.now())
    last_updated_ts = db.Column(db.DateTime, default=datetime.datetime.now())
    from_user = relationship('User', foreign_keys=[from_user_id])
    to_user = relationship('User', foreign_keys=[to_user_id])

    def __init__(self, from_user_id, to_user_id, description, amount):
        self.from_user_id = from_user_id
        self.to_user_id = to_user_id
        self.description = description
        self.amount = amount

    def to_dict(self):
        return {
            'id': self.id,
            'fromUserId': self.from_user_id,
            'toUserId': self.to_user_id,
            'description': self.description,
            'amount': self.amount,
            'fromUser': self.from_user.to_dict(),
            'toUser': self.to_user.to_dict(),
            'createdTS': self.created_ts,
            'lastUpdatedTS': self.last_updated_ts
        }
