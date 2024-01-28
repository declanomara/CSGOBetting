import sqlite3

from flask import Flask, g
from src.models import UnifiedMatch

app = Flask(__name__)

DB_PATH = "matches.db"

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)

    def make_dicts(cursor, row):
        return dict((cursor.description[idx][0], value)
                    for idx, value in enumerate(row))

    db.row_factory = make_dicts

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
    matches = get_db().execute("SELECT * FROM matches").fetchall()

    return {"matches": matches}

if __name__ == "__main__":
    app.run(port=5000, debug=True)