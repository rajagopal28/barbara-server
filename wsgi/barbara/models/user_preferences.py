from barbara import db
import datetime
from sqlalchemy.orm import relationship


class UserPreference(db.Model):
    __tablename__ = 'user_preferences'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    nick_name = db.Column(db.String(128))
    security_question = db.Column(db.String(128))
    budget = db.Column(db.Float, default=0.0)
    created_ts = db.Column(db.DateTime, default=datetime.datetime.now())
    last_updated_ts = db.Column(db.DateTime, default=datetime.datetime.now())
    user = relationship('User', back_populates='preferences')

    def __init__(self, user_id, nick_name=None, security_question=None, budget=0):
        self.user_id = user_id
        self.nick_name = nick_name
        self.security_question = security_question
        self.budget = budget

    def to_dict(self):
        return {
            'id': self.id,
            'userId': self.user_if,
            'nickName': self.nick_name,
            'securityQuestion': self.security_question,
            'budget': self.budget,
            'user': self.user.to_dict(),
            'createdTS': self.created_ts,
            'lastUpdatedTS': self.last_updated_ts,
        }
