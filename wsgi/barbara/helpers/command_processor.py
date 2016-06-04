import string
import datetime
import random

from barbara import app
from barbara.models.command_response import CommandResponse

ASSISTANT_NAME = app.config['ASSISTANT_NAME']

SPECIAL_CHARACTERS = [',', '.', ';', ':', '?', '!']
GREETING_TEXTS = ['hey', 'hello', 'hi']

DELIMITER_WHITE_SPACE = ' '

READ_COMMAND_IDENTIFIERS = ['what is', 'did i', 'have i']
READ_OPERATION_TYPE_SEND = ['send', 'transfer', 'pay', 'sent', 'transferred', 'paid']
READ_OPERATION_TYPE_RECEIVE = ['receive', 'got', 'get']

RELATIVE_TIME_REFERENCES = ['last week', 'last month', 'yesterday', 'today', 'tomorrow', 'next week', 'next month']
MONTHS_OF_YEAR = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october',
                  'november', 'december']

IDENTIFYING_SELF = ['me', 'my']
CURRENT_BALANCE_IDENTIFIERS = ['current', 'balance', 'outstanding', 'bill']
ACCOUNT_IDENTIFIER_CREDIT = ['credit', 'card']
IDENTIFIER_TO = 'to'
IDENTIFIER_FROM = 'from'
IDENTIFIER_ON = ' on '
DEFER_TRANSFER_IDENTIFIERS = ['schedule to', 'schedule']
REMINDER_IDENTIFIERS = ['remind me to', 'remind me', 'remind']
BUDGET_IDENTIFIERS = ['budget']
SET_BUDGET_IDENTIFIERS = ['set budget to']
PROMOTIONS_IDENTIFIERS = ['like to buy', 'promotions on']
PROMOTION_REPLACEMENT = 'promotion_content'
ACCOUNT_SELF = 'self'
AMOUNT_REFERENCE_NONE = 'money'
AMOUNT_REFERENCES = [{'hundred': 100}, {'thousand': 1000}, {'fifty': 50}, {'twenty': 20}, {'ten': 10}]
SARCASTIC_MIS_REPLIES = ['Oops! Seems like you missed a vowel there. ha ha ha. Try again.',
                         'I don\'t think a banking assistant can know that. Try again.',
                         'I\'m not that miraculous to do that. Try again']


def process_command(command_sentence):
    command_sentence = command_sentence.lower()
    command_response = CommandResponse(input_command=command_sentence)
    # check for greeting text
    command_sentence = remove_special_characters(command_sentence)
    command_response.has_greeting_text = is_greeting_present(command_sentence)
    command_sentence = remove_greetings_from_sentence(command_sentence)
    # remove assistant name
    command_sentence = remove_words_from_sentence(command_sentence, [ASSISTANT_NAME])
    # check command type
    command_response.is_read_request = check_read_request(command_sentence)
    command_response.is_transaction_request = check_transaction_request(command_sentence)
    command_response.is_schedule_request = is_deferred_transaction_request(command_sentence)
    command_response.is_reminder_request = is_reminder_request(command_sentence)
    # remove schedule identifiers
    command_sentence = replace_words_in_phrases(command_sentence, DEFER_TRANSFER_IDENTIFIERS)
    # remove reminder identifiers
    command_sentence = replace_words_in_phrases(command_sentence, REMINDER_IDENTIFIERS)
    command_response.is_current_balance_request = check_current_balance_request(command_sentence)
    command_response.is_credit_account = check_account_credit(command_sentence)
    if check_account_self(command_sentence):
        command_response.referred_user = ACCOUNT_SELF
    else:
        # get name from the string
        command_response.referred_user = extract_user_name_from_sentence(command_sentence)
    command_response.referred_amount = extract_amount_from_sentence(command_sentence)
    if command_response.referred_amount != AMOUNT_REFERENCE_NONE and not str(
            command_response.referred_amount).isdigit():
        command_response.referred_amount = get_number_to_text_amount(command_response.referred_amount)
    command_response.is_read_sent_transaction = check_read_sent_transaction(command_sentence)
    # is this promotions check
    command_response.is_promotions_check = check_promotions_enquiry(command_sentence)
    # remove promotion references
    command_sentence = remove_promotions_context_from_sentence(command_sentence)
    command_response.time_associated = get_time_from_reference(command_sentence)
    # remove time references
    command_sentence = remove_time_context_from_sentence(command_sentence)
    # is this budget check
    command_response.is_budget_check = check_budget_enquiry(command_sentence)
    command_response.is_budget_change = check_budget_change(command_sentence)
    command_response.response_text = get_message_for_response(command_response, command_sentence)
    return command_response


def get_message_for_response(command_response, command_sentence):
    message = None
    if command_response.is_promotions_check:
        message = extract_promotions_from_sentence(command_sentence).strip()
    elif command_response.is_budget_check and command_response.is_budget_change:
        message = extract_budget_from_sentence(command_sentence).strip()
    elif command_response.is_schedule_request:
        if command_response.referred_user and command_response.referred_amount:
            message = 'Reminder to transfer' + command_response.referred_amount \
                      + ' to ' + command_response.referred_user \
                      + ' on ' + str(command_response.time_associated)
        else:
            message = get_mis_replies()
    elif command_response.is_reminder_request:
        message = 'Reminder to ' + command_sentence \
                  + ' on ' + str(command_response.time_associated)
    elif command_response.is_schedule_request:
        if command_response.referred_amount and command_response.referred_user != ACCOUNT_SELF:
            message = 'Scheduling a transfer of ' + command_response.referred_amount \
                      + ' to ' + command_response.referred_user \
                      + ' on ' + str(command_response.time_associated)
        else:
            message = get_mis_replies()
    elif command_response.is_read_request:
        if command_response.is_credit_account and command_response.is_current_balance_request:
            message = 'Reading your credit card outstanding'
        elif command_response.is_current_balance_request:
            message = 'Reading your current account balance'
        elif command_response.is_read_sent_transaction:
            message = 'Reading your sent transaction to ' + command_response.referred_user \
                      + ' on ' + str(command_response.time_associated)
        elif command_response.referred_user != 'self':
            message = 'Reading your transaction from ' + command_response.referred_user \
                      + ' on ' + str(command_response.time_associated)

    elif command_response.is_transaction_request:
        if command_response.is_credit_account:
            message = 'Paying your credit card outstanding'
        else:
            message = 'Transferring ' + command_response.referred_amount + ' to ' \
                      + command_response.referred_user + ' now'
    else:
        message = get_mis_replies()
    return message


def remove_time_context_from_sentence(sentence):
    index = sentence.find(IDENTIFIER_ON)
    # remove absolute time reference
    if index != -1:
        sentence = sentence[0:index]
    sentence = remove_words_from_sentence(sentence, [IDENTIFIER_ON])
    return remove_words_from_sentence(sentence, RELATIVE_TIME_REFERENCES)


def index_of_item_in_list(list_to_search, item_to_search):
    _index = -1
    _te = [index for index, item in enumerate(list_to_search) if item == item_to_search]
    if len(_te) > 0:
        _index = _te[0]
    return _index


def remove_promotions_context_from_sentence(sentence):
    return remove_phrase_from_sentence(sentence, PROMOTIONS_IDENTIFIERS, PROMOTION_REPLACEMENT)


def extract_user_name_from_sentence(sentence):
    words = sentence.split()
    some_name_string = None
    index = index_of_item_in_list(words, IDENTIFIER_FROM)
    if index == -1:
        index = index_of_item_in_list(words, IDENTIFIER_TO)
    if index != -1 and len(words) > index:
        some_name_string = words[index + 1]
    return some_name_string


def extract_amount_from_sentence(sentence):
    words = sentence.split()
    some_name_string = None
    index = index_of_item_in_list(words, IDENTIFIER_FROM)
    if index == -1:
        index = index_of_item_in_list(words, IDENTIFIER_TO)
    if index != -1 and index > 0:
        some_name_string = words[index - 1]
    return some_name_string


def extract_promotions_from_sentence(sentence):
    chosen_word = DELIMITER_WHITE_SPACE
    found_index = sentence.find(PROMOTION_REPLACEMENT)
    if found_index != -1:
        chosen_word = sentence[found_index + len(PROMOTION_REPLACEMENT): len(sentence)]
    return chosen_word


def extract_budget_from_sentence(sentence):
    chosen_word = DELIMITER_WHITE_SPACE
    replacement = SET_BUDGET_IDENTIFIERS[0]
    found_index = sentence.find(replacement)
    if found_index != -1:
        chosen_word = sentence[found_index + len(replacement): len(sentence)]
    return chosen_word


def get_string_if_present_in_sentence(sentence, words_to_search):
    chosen_word = None
    _te = [word for word in words_to_search if check_sentence_has_words_in_list(sentence, [word])]
    if len(_te) > 0:
        chosen_word = _te[0]
    return chosen_word


def replace_words_in_phrases(sentence, words):
    for word in words:
        sentence = string.replace(sentence, word, DELIMITER_WHITE_SPACE)
    return sentence.strip()


def get_time_from_reference(sentence):
    index = sentence.find(IDENTIFIER_ON)
    now = datetime.date.today()
    # eod_time = datetime.time(23, 59, 0)
    date_reference = now
    if index != -1:
        # absolute reference
        some_time_string = sentence[index + 3: len(sentence)]  # till end of sentence
        splits = some_time_string.strip().split()
        day_ref = int(splits[0])
        month_ref = splits[1]
        month_index = index_of_item_in_list(MONTHS_OF_YEAR, month_ref)
        current_year = now.year
        if month_index > now.month:
            current_year -= 1
        date_reference = datetime.date(current_year, month_index + 1, day_ref)
        # 24 JAN
    else:
        # relative reference
        time_reference = get_string_if_present_in_sentence(sentence, RELATIVE_TIME_REFERENCES)
        if time_reference:
            # check what the reference is
            if time_reference == 'yesterday':
                date_reference = now - datetime.timedelta(days=1)
            elif time_reference == 'tomorrow':
                date_reference = now + datetime.timedelta(days=1)
            elif time_reference == 'last week':
                date_reference = now - datetime.timedelta(days=7)
            elif time_reference == 'last month':
                date_reference = now - datetime.timedelta(days=30)
            elif time_reference == 'this month':
                date_reference = now - datetime.timedelta(days=now.day)
            elif time_reference == 'this week':
                date_reference = now - datetime.timedelta(days=now.weekday())
            elif time_reference == 'next week':
                date_reference = now + datetime.timedelta(days=7)
            elif time_reference == 'next month':
                date_reference = now + datetime.timedelta(days=30)
    # date_reference = datetime.datetime.combine(date_reference, eod_time)  # set time to end ot day i.e., 23:59:00
    return date_reference


def check_read_sent_transaction(command_sentence):
    return check_sentence_has_words_in_list(command_sentence, READ_OPERATION_TYPE_SEND)


def check_account_credit(command_sentence):
    return check_sentence_has_words_in_list(command_sentence, ACCOUNT_IDENTIFIER_CREDIT)


def check_account_self(command_sentence):
    return check_sentence_has_words_in_list(command_sentence, IDENTIFYING_SELF)


def check_current_balance_request(sentence):
    return check_sentence_has_words_in_list(sentence, CURRENT_BALANCE_IDENTIFIERS)


def check_read_request(sentence):
    return check_sentence_has_words_in_list(sentence, READ_COMMAND_IDENTIFIERS)


def check_transaction_request(sentence):
    return check_sentence_has_words_in_list(sentence, READ_OPERATION_TYPE_SEND)


def check_budget_enquiry(sentence):
    return check_sentence_has_words_in_list(sentence, BUDGET_IDENTIFIERS)


def check_budget_change(sentence):
    return check_sentence_has_words_in_list(sentence, SET_BUDGET_IDENTIFIERS)


def check_promotions_enquiry(sentence):
    return check_sentence_has_words_in_list(sentence, PROMOTIONS_IDENTIFIERS)


def is_greeting_present(sentence):
    return check_sentence_has_words_in_list(sentence, GREETING_TEXTS)


def is_deferred_transaction_request(sentence):
    return check_sentence_has_words_in_list(sentence, DEFER_TRANSFER_IDENTIFIERS)


def is_reminder_request(sentence):
    return check_sentence_has_words_in_list(sentence, REMINDER_IDENTIFIERS)


def check_sentence_has_words_in_list(sentence, words_list):
    return any(with_word_boundary(word) in with_word_boundary(sentence) for word in words_list)


def with_word_boundary(word):
    return ' %s ' % word


def remove_words_from_sentence(sentence, words_to_remove):
    return DELIMITER_WHITE_SPACE.join([i for i in sentence.split() if i not in words_to_remove])


def remove_phrase_from_sentence(sentence, phrases_to_remove, replacement=''):
    for phrase in phrases_to_remove:
        sentence = sentence.replace(phrase, replacement)
    return sentence


def remove_greetings_from_sentence(sentence):
    return remove_words_from_sentence(sentence, GREETING_TEXTS)


def remove_special_characters(sentence):
    chars_to_remove = set(SPECIAL_CHARACTERS)
    return ''.join([c for c in sentence if c not in chars_to_remove])


def find_substring(needle, haystack):
    index = haystack.find(needle)
    if index == -1:
        return False
    if index != 0 and haystack[index - 1] not in string.whitespace:
        return False
    L = index + len(needle)
    if L < len(haystack) and haystack[L] not in string.whitespace:
        return False
    return True


def get_number_to_text_amount(amount_text):
    for item in AMOUNT_REFERENCES:
        if item.get(amount_text):
            return item[amount_text]
    return None


def get_mis_replies():
    index = int(100 * random.random()) % len(SARCASTIC_MIS_REPLIES)
    return SARCASTIC_MIS_REPLIES[index]


def text_to_int(text_num, num_words={}):
    if not num_words:
        units = [
            "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
            "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
            "sixteen", "seventeen", "eighteen", "nineteen",
        ]

        tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

        scales = ["hundred", "thousand", "million", "billion", "trillion"]

        num_words["and"] = (1, 0)
        for idx, word in enumerate(units):    num_words[word] = (1, idx)
        for idx, word in enumerate(tens):     num_words[word] = (1, idx * 10)
        for idx, word in enumerate(scales):   num_words[word] = (10 ** (idx * 3 or 2), 0)

    current = result = 0
    for word in text_num.split():
        if word not in num_words:
            raise Exception("Illegal word: " + word)

        scale, increment = num_words[word]
        current = current * scale + increment
        if scale > 100:
            result += current
            current = 0

    return result + current
