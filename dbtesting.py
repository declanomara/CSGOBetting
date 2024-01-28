import sqlite3

from models import UnifiedMatch
import json

class Database:
    def __init__(self, path):
        self._conn = sqlite3.connect(path)
        self._cur = self._conn.cursor()
        self._cur.execute('''CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lounge_time INTEGER,
            lounge_status TEXT,
            lounge_team1 TEXT,
            lounge_team2 TEXT,
            lounge_t1_value REAL,
            lounge_t2_value REAL,
            bovada_time INTEGER,
            bovada_team1 TEXT,
            bovada_team2 TEXT,
            bovada_t1_moneyline REAL,
            bovada_t2_moneyline REAL,
            UNIQUE(lounge_time, lounge_status, lounge_team1, lounge_team2, lounge_t1_value, lounge_t2_value, bovada_time, bovada_team1, bovada_team2, bovada_t1_moneyline, bovada_t2_moneyline)
        )''')
        self._conn.commit()

    def insert_match(self, match: UnifiedMatch):
        serialized = match.serialize()
        query = "INSERT INTO matches (lounge_time, lounge_status, lounge_team1, lounge_team2, lounge_t1_value, lounge_t2_value, bovada_time, bovada_team1, bovada_team2, bovada_t1_moneyline, bovada_t2_moneyline) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        self._cur.execute(query, (
            serialized['lounge_time'],
            serialized['lounge_status'],
            serialized['lounge_team1'],
            serialized['lounge_team2'],
            serialized['lounge_t1_value'],
            serialized['lounge_t2_value'],
            serialized['bovada_time'],
            serialized['bovada_team1'],
            serialized['bovada_team2'],
            serialized['bovada_t1_moneyline'],
            serialized['bovada_t2_moneyline']
        ))
        self._conn.commit()

    def get_matches_after_time(self, time):
        query = "SELECT * FROM matches WHERE lounge_time > ?"
        self._cur.execute(query, (time,))
        rows = self._cur.fetchall()
        matches = []
        for row in rows:
            serialized = {
                'lounge_time': row[1],
                'lounge_status': row[2],
                'lounge_team1': row[3],
                'lounge_team2': row[4],
                'lounge_t1_value': row[5],
                'lounge_t2_value': row[6],
                'bovada_time': row[7],
                'bovada_team1': row[8],
                'bovada_team2': row[9],
                'bovada_t1_moneyline': row[10],
                'bovada_t2_moneyline': row[11]
            }
            match = UnifiedMatch.deserialize(serialized)
            matches.append(match)
        return matches

    def get_matches(self):
        query = "SELECT * FROM matches"
        self._cur.execute(query)
        rows = self._cur.fetchall()
        matches = []
        for row in rows:
            serialized = {
                'lounge_time': row[1],
                'lounge_status': row[2],
                'lounge_team1': row[3],
                'lounge_team2': row[4],
                'lounge_t1_value': row[5],
                'lounge_t2_value': row[6],
                'bovada_time': row[7],
                'bovada_team1': row[8],
                'bovada_team2': row[9],
                'bovada_t1_moneyline': row[10],
                'bovada_t2_moneyline': row[11]
            }
            match = UnifiedMatch.deserialize(serialized)
            matches.append(match)
        return matches

def create_dummy_match():
    serialized = {'lounge_time': 1706527806, 'lounge_status': 0, 'lounge_team1': 'Bleed', 'lounge_team2': 'Metizport', 'lounge_t1_value': 0.22, 'lounge_t2_value': 0.044, 'bovada_time': 1706527800, 'bovada_team1': 'Bleed', 'bovada_team2': 'Metizport', 'bovada_t1_moneyline': -175.0, 'bovada_t2_moneyline': 135.0}
    return UnifiedMatch.deserialize(serialized)

def main():
    DB_PATH = 'matches.db'
    db = Database(DB_PATH)
    match = create_dummy_match()
    db.insert_match(match)
    matches = db.get_matches()
    print(matches)


if __name__ == "__main__":
    main()