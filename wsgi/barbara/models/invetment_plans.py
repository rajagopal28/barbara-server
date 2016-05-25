from barbara import db
from sqlalchemy.orm import relationship
import datetime


class InvestmentPlan(db.Model):
    __tablename__ = 'investment_plans'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(128))
    amount = db.Column(db.Float)
    created_ts = db.Column(db.DateTime, default=datetime.datetime.now())
    last_updated_ts = db.Column(db.DateTime, default=datetime.datetime.now())

    def __init__(self, description, amount):
        self.amount = amount
        self.description = description

    def to_dict(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'description': self.description,
            'createdTS': self.created_ts,
            'lastUpdatedTS': self.last_updated_ts
        }