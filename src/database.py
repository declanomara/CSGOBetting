import sqlite3

from models import UnifiedMatch

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

    def _row_to_match(self, row):
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
        return UnifiedMatch.deserialize(serialized)

    def insert_match(self, match: UnifiedMatch):
        serialized = match.serialize()
        query = "INSERT INTO matches (lounge_time, lounge_status, lounge_team1, lounge_team2, lounge_t1_value, lounge_t2_value, bovada_time, bovada_team1, bovada_team2, bovada_t1_moneyline, bovada_t2_moneyline) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        
        try:
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
            return True
        except sqlite3.IntegrityError:
            # Duplicate entry
            return False

    def update_match(self, match: UnifiedMatch):
        # Update the match in the database with the same lounge_time and bovada_time
        serialized = match.serialize()
        query = "UPDATE matches SET lounge_status = ?, lounge_t1_value = ?, lounge_t2_value = ?, bovada_t1_moneyline = ?, bovada_t2_moneyline = ? WHERE lounge_time = ? AND bovada_time = ?"
        try:
            self._cur.execute(query, (
                serialized['lounge_status'],
                serialized['lounge_t1_value'],
                serialized['lounge_t2_value'],
                serialized['bovada_t1_moneyline'],
                serialized['bovada_t2_moneyline'],
                serialized['lounge_time'],
                serialized['bovada_time']
            ))
            self._conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Duplicate entry
            return False

    def close(self):
        self._conn.close()

    def get_matches_after_time(self, time):
        query = "SELECT * FROM matches WHERE lounge_time > ?"
        self._cur.execute(query, (time,))
        rows = self._cur.fetchall()
        matches = []
        for row in rows:
            match = self._row_to_match(row)
            matches.append(match)
        return matches

    def get_matches(self):
        # Return all matches in the database in order of bovada_time
        query = "SELECT * FROM matches"
        self._cur.execute(query)
        rows = self._cur.fetchall()
        matches = []
        for row in rows:
            match = self._row_to_match(row)
            matches.append(match)
        return matches
    
    def get_matches_by_status(self, status):
        query = "SELECT * FROM matches WHERE lounge_status = ?"
        self._cur.execute(query, (status,))
        rows = self._cur.fetchall()
        matches = []
        for row in rows:
            match = self._row_to_match(row)
            matches.append(match)
        return matches
    
    def get_matches_by_team(self, team):
        # Return all matches that {team} is playing in, regardless of if they are team1 or team2
        query = "SELECT * FROM matches WHERE lounge_team1 = ? OR lounge_team2 = ?"
        self._cur.execute(query, (team, team))
        rows = self._cur.fetchall()
        matches = []
        for row in rows:
            match = self._row_to_match(row)
            matches.append(match)
        return matches
    
    def get_matches_by_teams(self, team1, team2):
        # Return all matches with {team1} and {team2} playing against each other
        query = "SELECT * FROM matches WHERE (lounge_team1 = ? AND lounge_team2 = ?) OR (lounge_team1 = ? AND lounge_team2 = ?)"
        self._cur.execute(query, (team1, team2, team2, team1))
        rows = self._cur.fetchall()
        matches = []
        for row in rows:
            match = self._row_to_match(row)
            matches.append(match)
        return matches
    
    def count(self):
        # Return the number of matches in the database
        query = "SELECT COUNT(*) FROM matches"
        self._cur.execute(query)
        return self._cur.fetchone()[0]
    
