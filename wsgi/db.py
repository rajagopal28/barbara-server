from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from barbara import app, db
from barbara.config import SQLALCHEMY_DATABASE_URI

migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
