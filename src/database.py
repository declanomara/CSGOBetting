import sqlite3

try:
    from .models import UnifiedMatch, Bet
except ImportError:
    from models import UnifiedMatch, Bet

class Database:
    def __init__(self, path, auto_connect=True, auto_init=True):
        self.path = path
        self._conn = None
        self._cur = None

        if auto_connect:
            self.connect()
        
        if auto_init:
            self.init()
        
    def connect(self):
        self._conn = sqlite3.connect(self.path)
        self._cur = self._conn.cursor()

    def init(self):
        if self._cur is None:
            raise Exception("Database not connected")
        
        # Create the matches table if it does not exist
        self._cur.execute('''CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY,
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
            last_updated INTEGER,
            UNIQUE(lounge_time, bovada_time, lounge_team1, lounge_team2, bovada_team1, bovada_team2)
        )''')

        # Create the bets table if it does not exist
        self._cur.execute('''
            CREATE TABLE IF NOT EXISTS bets (
                match_id INT PRIMARY KEY,
                side INT,
                amount FLOAT,
                time INT
        )''')

        # Create the archive table if it does not exist
        self._cur.execute('''
            CREATE TABLE IF NOT EXISTS archive (
                id INT,
                lounge_time INT,
                lounge_status TEXT,
                lounge_team1 TEXT,
                lounge_team2 TEXT,
                lounge_t1_value REAL,
                lounge_t2_value REAL,
                bovada_time INT,
                bovada_team1 TEXT,
                bovada_team2 TEXT,
                bovada_t1_moneyline REAL,
                bovada_t2_moneyline REAL,
                last_updated INT,
                PRIMARY KEY (id, last_updated)
        )''')

        query = "CREATE INDEX IF NOT EXISTS index_id ON archive (id)"
        self._cur.execute(query)
        self._conn.commit()

    def _row_to_match(self, row):
        serialized = {
            'lounge_id': row[0],
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
            'bovada_t2_moneyline': row[11],
            'last_updated': row[12]
        }
        return UnifiedMatch.deserialize(serialized)

    def insert_match(self, match: UnifiedMatch):
        serialized = match.serialize()
        query = "INSERT INTO matches (id, lounge_time, lounge_status, lounge_team1, lounge_team2, lounge_t1_value, lounge_t2_value, bovada_time, bovada_team1, bovada_team2, bovada_t1_moneyline, bovada_t2_moneyline, last_updated) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        
        try:
            self._cur.execute(query, (
                serialized['lounge_id'],
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
                serialized['bovada_t2_moneyline'],
                serialized['last_updated']
            ))
            self._conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Duplicate entry
            return False

    def update_match(self, match: UnifiedMatch):
        # Update the match in the database with the same id
        self.archive(match.lounge_id)
        serialized = match.serialize()
        query = "UPDATE matches SET lounge_time = ?, lounge_status = ?, lounge_t1_value = ?, lounge_t2_value = ?, bovada_time = ?, bovada_t1_moneyline = ?, bovada_t2_moneyline = ?, last_updated = ? WHERE id = ?"
        try:
            self._cur.execute(query, (
                serialized['lounge_time'],
                serialized['lounge_status'],
                serialized['lounge_t1_value'],
                serialized['lounge_t2_value'],
                serialized['bovada_time'],
                serialized['bovada_t1_moneyline'],
                serialized['bovada_t2_moneyline'],
                serialized['last_updated'],
                serialized['lounge_id']
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

    def get_matches_before_time(self, time):
        query = "SELECT * FROM matches WHERE lounge_time < ?"
        self._cur.execute(query, (time,))
        rows = self._cur.fetchall()
        matches = []
        for row in rows:
            match = self._row_to_match(row)
            matches.append(match)
        return matches
    
    def get_matches_between_times(self, start, end):
        query = "SELECT * FROM matches WHERE lounge_time > ? AND lounge_time < ?"
        self._cur.execute(query, (start, end))
        rows = self._cur.fetchall()
        matches = []
        for row in rows:
            match = self._row_to_match(row)
            matches.append(match)
        return matches
    
    def get_matches(self):
        # Return all matches in the database in order of bovada_time
        query = "SELECT * FROM matches ORDER BY bovada_time ASC"
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
    
    def get_match_by_id(self, match_id):
        query = "SELECT * FROM matches WHERE id = ?"
        self._cur.execute(query, (match_id,))
        row = self._cur.fetchone()
        if row is None:
            return None
        return self._row_to_match(row)
    
    def count_matches(self):
        # Return the number of matches in the database
        query = "SELECT COUNT(*) FROM matches"
        self._cur.execute(query)
        return self._cur.fetchone()[0]
    
    def _row_to_bet(self, row):
        return Bet(
            match_id=row[0],
            side=row[1],
            amount=row[2],
            time_placed=row[3]
        )
    
    def get_bets(self):
        # Return all bets in the database in order of time placed (newest first)
        query = "SELECT * FROM bets ORDER BY time ASC"
        self._cur.execute(query)
        rows = self._cur.fetchall()
        return [self._row_to_bet(row) for row in rows]
    
    def get_bet_by_match_id(self, match_id):
        query = "SELECT * FROM bets WHERE match_id = ?"
        self._cur.execute(query, (match_id,))
        row = self._cur.fetchone()
        if row is None:
            return None
        return self._row_to_bet(row)
    
    def count_bets(self):
        # Return the number of bets in the database
        query = "SELECT COUNT(*) FROM bets"
        self._cur.execute(query)
        return self._cur.fetchone()[0]
    
    def insert_bet(self, bet):
        # Insert a bet into the database
        query = "INSERT INTO bets (match_id, side, amount, time) VALUES (?, ?, ?, ?)"
        self._cur.execute(query, (bet.match_id, bet.side, bet.amount, bet.time_placed))
        self._conn.commit()

    def update_bet(self, bet):
        # Update a bet in the database
        query = "UPDATE bets SET side = ?, amount = ?, time = ? WHERE match_id = ?"
        self._cur.execute(query, (bet.side, bet.amount, bet.time_placed, bet.match_id))
        self._conn.commit()

    def delete_bet_by_match_id(self, match_id):
        query = "DELETE FROM bets WHERE match_id = ?"
        self._cur.execute(query, (match_id,))
        self._conn.commit()

    def archive(self, match_id):
        # Archive a match by copying it to the archive table
        query = "SELECT * FROM matches WHERE id = ?"
        self._cur.execute(query, (match_id,))
        row = self._cur.fetchone()
        if row is None:
            return False
        
        query = """
        INSERT INTO archive (
            id, lounge_time, lounge_status, lounge_team1, lounge_team2, lounge_t1_value, lounge_t2_value, bovada_time, bovada_team1, bovada_team2, bovada_t1_moneyline, bovada_t2_moneyline, last_updated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self._cur.execute(query, row)
        self._conn.commit()

        return True
    
    def get_historical_matches_by_id(self, match_id, after=None, before=None):
        # Return the time series changes for a match from the archive table
        # Simply gather all rows with the same match_id in order of last_updated

        query = "SELECT * FROM archive WHERE id = ?"
        params = [match_id]

        if after:
            query += " AND last_updated > ?"
            params.append(after)

        if before:
            query += " AND last_updated < ?"
            params.append(before)

        query += " ORDER BY last_updated ASC"

        self._cur.execute(query, params)
        rows = self._cur.fetchall()
        matches = []
        for row in rows:
            match = self._row_to_match(row)
            matches.append(match)

        return matches
    


