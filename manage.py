#!flask/bin/python
"""flask manager with commands for miyagi."""
from tags import manager, Tag
from flask.ext.migrate import MigrateCommand

manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
