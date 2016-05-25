#!/usr/bin/env python

import sys
import imaplib
import email
import datetime

from barbara import app

USER_EMAIL = app.config['USER_EMAIL_FOR_PROMOTIONS']
USER_PASSWORD = app.config['USER_EMAIL_PASSWORD']
EMAIL_LABEL = 'INBOX'
SEARCH_TYPE_ALL = 'ALL'
SORT_RECENT_FIRST = 'REVERSE DATE'  # Descending, most recent email first
ENCODING_UTF_8 = 'UTF-8'
MAIL_TIME_FRAME = 30  # <-- days one month email only


def read_email(search_pattern):
    MAIL_BOX = imaplib.IMAP4_SSL('imap.gmail.com')
    search_response = None
    try:
        MAIL_BOX.login(USER_EMAIL, USER_PASSWORD)
    except imaplib.IMAP4.error:
        print "LOGIN FAILED!!! "
        return
        # ... exit or deal with failure...
    rv, mailboxes = MAIL_BOX.list()
    if rv == 'OK':
        print "Mailboxes:"
        print mailboxes
    rv, data = MAIL_BOX.select(EMAIL_LABEL)
    if rv == 'OK':
        print "Processing mailbox...\n"
        search_response = process_mailbox(MAIL_BOX, search_pattern)  # ... do something with emails, see below ...
        MAIL_BOX.close()
    MAIL_BOX.logout()
    return search_response


# Note: This function definition needs to be placed
#       before the previous block of code that calls it.
def process_mailbox(MAIL_BOX_INSTANCE, search_pattern):
    # regex = r'(X-GM-RAW "subject:\"%s\"")' % search_pattern
    search_response = []
    print search_pattern
    date = (datetime.date.today() - datetime.timedelta(MAIL_TIME_FRAME)).strftime("%d-%b-%Y")
    rv, data = MAIL_BOX_INSTANCE.search(None, SEARCH_TYPE_ALL,
                        '(SENTSINCE {date} HEADER Subject "{subject_pattern}")'
                                        .format(date=date, subject_pattern=search_pattern))
    # M.sort(SORT_RECENT_FIRST, ENCODING_UTF_8, SEARCH_TYPE_ALL, regex)  #
    if rv != 'OK':
        print "No messages found!"
        return

    for num in data[0].split():
        rv, data = MAIL_BOX_INSTANCE.fetch(num, '(RFC822)')
        if rv != 'OK':
            print "ERROR getting message", num
            return

        msg = email.message_from_string(data[0][1])
        print 'Message %s: %s' % (num, msg['Subject'])
        print 'Raw Date:', msg['Date']
        search_response.append(msg['Subject'])
        date_tuple = email.utils.parsedate_tz(msg['Date'])
        if date_tuple:
            local_date = datetime.datetime.fromtimestamp(
                    email.utils.mktime_tz(date_tuple))
            print "Local Date:", \
                local_date.strftime("%a, %d %b %Y %H:%M:%S")
    return search_response
