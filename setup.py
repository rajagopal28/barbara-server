from setuptools import setup

setup(name='BarbaraApplication',
      version='1.0',
      description='Server of barbara banking application',
      author='Rajagopal M',
      author_email='rajagopal.a.dinesh.28@gmail.com',
      url='http://www.python.org/sigs/distutils-sig/',
      install_requires=['gevent', 'Flask', 'MarkupSafe', 'Flask-SQLAlchemy', 'Flask-Migrate', 'mysqlclient',
                        'werkzeug'],
      py_modules=[]
      )
