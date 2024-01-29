import requests
import json
import pytz
import time
import argparse

from datetime import datetime
from src.database import Database
from src.models import BovadaMatch, LoungeMatch, UnifiedMatch

BOVADA_URL = "https://www.bovada.lv/services/sports/event/coupon/events/A/description/esports/counter-strike-2"
LOUNGE_URL = "https://csgolounge.com"
OUT_FILE = "matches.txt"

def datetime_to_timestamp(dt):
    # Take a datetime object and convert it to a timestamp in the format Monday, January 01 (00:00AM PST)
    
    # Convert to PST
    pst = pytz.timezone("America/Los_Angeles")
    dt = dt.astimezone(pst)

    # Convert to timestamp
    return dt.strftime('%A, %B %d (%I:%M%p %Z)')


def get_bovada_matches(session):
    response = session.get(BOVADA_URL)

    # TODO: Handle errors

    events = []
    for obj in response.json():
        events.extend(obj["events"])

    bovada_matches = []
    for event in events:
        if len(event["competitors"]) != 2:
            continue    

        bovada_matches.append(BovadaMatch.from_event(event))
    
    return bovada_matches


def parse_lounge_matches(html):
    # Extract the JSON data from the function call in the HTML
    # The line looks like this:
    # this.populateBets([{...}, {...}, ..., {...}]);

    # Find the start of the JSON data
    start = html.find("this.populateBets(")
    start += len("this.populateBets(")

    # Find the end of the JSON data
    end = html.find(");", start)

    # Extract the JSON data
    json_data = html[start:end]

    # Parse the JSON data
    return json.loads(json_data)


def get_lounge_matches(session):
    response = session.get(LOUNGE_URL)

    # TODO: Handle errors

    lounge_data = parse_lounge_matches(response.text)
    return [LoungeMatch.from_dict(match) for match in lounge_data if int(match["m_status"]) == 0]


def pair_matches(bovada_matches, lounge_matches):
    unpaired = []
    pairs = []

    for bm in bovada_matches:
        # Find the corresponding LoungeMatch
        least_diff = 1e9
        closest_match = None
        for lm in lounge_matches:
            diff = abs(lm.time - bm.time)
            if diff < least_diff and lm.team1 == bm.team1 and lm.team2 == bm.team2:
                least_diff = diff
                closest_match = lm

        # If no match was found, try reversing the teams
        if closest_match is None:
            
            bm = bm.reversed()
            for lm in lounge_matches:
                diff = abs(lm.time - bm.time)
                if diff < least_diff and lm.team1 == bm.team1 and lm.team2 == bm.team2:
                    least_diff = diff
                    closest_match = lm
        
        # If no match was found after reversing the teams, add to unpaired
        if closest_match is None:
            unpaired.append(bm)
            continue
        else:
            pairs.append((bm, closest_match))

    return pairs, unpaired


def unify_matches(pairs):
    now = int(time.time())
    return [UnifiedMatch(bm, lm, now) for bm, lm in pairs]


def update_matches(session, db: Database):
    # Get Bovada matches
    bovada_matches = get_bovada_matches(session)

    # Get CSGOLounge matches
    lounge_matches = get_lounge_matches(session)

    # Pair matches
    paired_matches, unpaired_matches = pair_matches(bovada_matches, lounge_matches)

    # Unify matches into general format containing all information
    unified_matches = unify_matches(paired_matches)

    # Add matches to database
    additions = 0
    updates = 0
    for match in unified_matches:
        success = db.insert_match(match)
        if success:
            additions += 1
            continue

        success = db.update_match(match)
        if success:
            updates += 1
            continue

    # Return the number of matches that were added
    return additions, updates


def main(database_dir):
    # Create session
    session = requests.Session()

    # Make session look like a browser
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 \
        (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36'
    })

    # Create database
    db = Database(database_dir)

    # Update matches
    print(f"Updating matches at {datetime_to_timestamp(datetime.now())}...")
    additions, updates = update_matches(session, db)
    print(f"Added {additions} matches to the database and updated {updates} existing records.")
    print(f"Done at {datetime_to_timestamp(datetime.now())}.")

    # Close session
    session.close()

    print(f"Database now contains {db.count()} matches.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='CSGO Betting')
    parser.add_argument('database_dir', type=str, help='Path to the database directory')
    args = parser.parse_args()

    main(args.database_dir)
