from os import environ

# Add your connection string
SQLALCHEMY_DATABASE_URI = 'mysql://root:@localhost/barbara_bank_db'
SQLALCHEMY_ECHO = False
MICROSOFT_SPEAKER_RECOGNITION_KEY = '75819815fa8e4b7aaeedcf1ebd7ba06c'
MICROSOFT_SPEAKER_RECOGNITION_KEY_2 = 'fb82ea53de2b42a4ba5198c07f4758fc'
UPLOAD_FOLDER = '/tmp'
DEFAULT_LOCALE = 'en-IN'
SECRET_KEY = 'L0nd0n6rIdg3i5F@11ingD0wn'
DEBUG = True
ASSISTANT_NAME = 'Barbara'

# manipulate the environmental configs from OPENSHIFT here
if 'OPENSHIFT_MYSQL_DB_URL' in environ:
    SQLALCHEMY_DATABASE_URI = environ['OPENSHIFT_MYSQL_DB_URL'] + environ['OPENSHIFT_APP_NAME']
