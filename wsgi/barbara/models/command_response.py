from barbara import db
import datetime


class CommandResponse(db.Model):
    __tablename__ = 'processed_commands'
    id = db.Column(db.Integer, primary_key=True)
    has_greeting_text = db.Column(db.Boolean, default=False)
    is_read_request = db.Column(db.Boolean, default=False)
    is_read_sent_transaction = db.Column(db.Boolean, default=False)  # true for send operations and false of receive
    is_current_balance_request = db.Column(db.Boolean, default=False)
    is_transaction_request = db.Column(db.Boolean, default=False)
    is_schedule_request = db.Column(db.Boolean, default=False)
    is_reminder_request = db.Column(db.Boolean, default=False)
    is_credit_account = db.Column(db.Boolean, default=False)
    is_budget_check = db.Column(db.Boolean, default=False)
    is_budget_change = db.Column(db.Boolean, default=False)
    is_promotions_check = db.Column(db.Boolean, default=False)
    referred_user = db.Column(db.String(128))
    referred_amount = db.Column(db.String(128))
    response_text = db.Column(db.String(128))
    time_associated = db.Column(db.String(128))
    scheduled_response_text = None
    created_ts = db.Column(db.DateTime, default=datetime.datetime.now())
    last_updated_ts = db.Column(db.DateTime, default=datetime.datetime.now())

    def __init__(self):
        pass

    def to_dict(self):
        return {
            'hasGreetingText': self.has_greeting_text,
            'isReadRequest': self.is_read_request,
            'isReadSentTransaction': self.is_read_sent_transaction,
            'isCurrentBalanceRequest': self.is_current_balance_request,
            'isTransactionRequest': self.is_transaction_request,
            'isScheduleRequest': self.is_schedule_request,
            'isReminderRequest': self.is_reminder_request,
            'isCreditAccount': self.is_credit_account,
            'isBudgetCheck': self.is_budget_check,
            'isBudgetChange': self.is_budget_change,
            'isPromotionsCheck': self.is_promotions_check,
            'requireAuthentication': self.is_schedule_request or self.is_transaction_request,
            'referredUser': self.referred_user,
            'referredAmount': self.referred_amount,
            'responseText': self.response_text,
            'associatedTime': str(self.time_associated),
            'scheduledResponseText': self.scheduled_response_text,
        }
