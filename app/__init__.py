from flask import Flask, g
from config import Config
import sqlite3

app = Flask(__name__)
app.config.from_object(Config)  # Use the Config class within config.py to provide the app's config settings

# Define functions required to get threaded database object

def connect_db():
    rv = sqlite3.connect(app.config['DATABASE_PATH'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


from app import fb_objects, routes, tests
