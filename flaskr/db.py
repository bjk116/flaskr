import sqlite3

import click
from flask import current_app, g
from flask.cli import with_appcontext

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_db(dict_factory=False):
	if  'db' not in g:
		g.db = sqlite3.connect(
				current_app.config['DATABASE'],
				detect_types=sqlite3.PARSE_DECLTYPES
			)

	if dict_factory:
		g.db.row_factory = dict_factory
	else:
		g.db.row_factory = sqlite3.Row

	return g.db

def close_db(e=None):
	db = g.pop('db', None)

	if db is not None:
		db.close()

def init_db():
	db = get_db()

	with current_app.open_resource('schema.sql') as f:
		db.executescript(f.read().decode('utf8'))

@click.command('init-db')
@with_appcontext
def init_db_command():
	"""Clear the existing data and creates new tables."""
	init_db()
	click.echo('Initialized the database.')

def init_app(app):
	# tells appp to call close_db after returning a response
	app.teardown_appcontext(close_db)
	# adds command that can be called with flask command
	app.cli.add_command(init_db_command)
