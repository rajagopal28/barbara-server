class CommandResponse():
    has_greeting_text = False
    is_read_request = False
    is_read_sent_transaction = False  # true for send operations and false of receive
    is_current_balance_request = False
    is_transaction_request = False
    is_schedule_request = False
    is_reminder_request = False
    is_credit_account = False
    is_budget_check = False
    is_budget_change = False
    is_promotions_check = False
    referred_user = None
    referred_amount = None
    response_text = None
    time_associated = None
    scheduled_response_text = None

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
            'referredUser': self.referred_user,
            'referredAmount': self.referred_amount,
            'responseText': self.response_text,
            'associatedTime': str(self.time_associated),
            'scheduledResponseText': self.scheduled_response_text,
        }
