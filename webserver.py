import sqlite3

from flask import Flask, g, render_template
from src.models import UnifiedMatch
from main import datetime_to_timestamp
from src.database import Database

app = Flask(__name__)

DB_PATH = "matches.db"

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        # db = g._database = sqlite3.connect(DB_PATH)
        # Use Database class instead of sqlite3.connect
        db = g._database = Database(DB_PATH)

    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/matches")
def matches():
    matches = get_db().get_matches()

    return render_template("matches.html", matches=matches, datetime_to_timestamp=datetime_to_timestamp)


if __name__ == "__main__":
    app.run(port=5000, debug=True)
