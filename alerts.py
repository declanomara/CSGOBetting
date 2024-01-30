# This script will check the status of upcoming matches through our API and send a notification if a high EV match is found.

import requests
import json
import time

from pprint import pprint
from src.database import Database


URL = "http://dserver:8000"
LOUNGE_URL = "https://csgolounge.com/"
LOCAL_DB_PATH = "matches.db"

def seconds_to_readable(seconds):
    # Return the number of seconds in a human-readable format
    # Xh Xm Xs
    hours = seconds // 3600
    seconds -= hours * 3600
    minutes = seconds // 60
    seconds -= minutes * 60

    # Only include hours and minutes if they are nonzero
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def timestamp_to_english(timestamp):
    # Return the time stamp in the format:
    # Monday, January 1st, 8:00 AM PST
    return time.strftime("%A, %B %d, %I:%M%p %Z", time.localtime(timestamp))

def gather_matches(timeframe=60*5):
    # Only check matches that start within the next 5 minutes
    now = int(time.time())
    time_threshold = now + timeframe

    endpoint = f"/matches?before={time_threshold}&after={now}"
    response = requests.get(URL + endpoint)
    matches = json.loads(response.text)
    return matches

def gather_local_matches(timeframe=60*5):
    # Only check matches that start within the next 5 minutes
    now = int(time.time())
    time_threshold = now + timeframe

    db = Database(LOCAL_DB_PATH)
    matches = db.get_matches_between_times(now, time_threshold)

    matches = [matches.to_JSON() for matches in matches]
    # Convert the datetime objects to %Y-%m-%dT%H:%M:%S
    for match in matches:
        match["time"] = match["time"].strftime("%Y-%m-%dT%H:%M:%S")

    return matches


def send_notification(message):
    pass

def most_profitable(match):
    # Return the winner of the match
    # 0 if team 1 wins, 1 if team 2 wins

    # If the match is finished, return the team with the highest score
    if match["expected_value"][0] > match["expected_value"][1]:
        return 0
    else:
        return 1
    
    # Same as above, but in one line (less readable?)
    # return int(match["score"][0] > match["score"][1])

def place_bet(session, match, side, amount):
    # Place a bet on {team} for {amount} dollars
    # {team} is 0 or 1
    # {amount} is in dollars

    id = match["id"]
    key = "uaovMUuAWEoZbd1lorrm255"
    endpoint = f"/index/placebet/{id}/{side}/{amount}/{key}/"
    cookie = "dark_theme=0; timezone=+0100; PHPSESSID=0ou5iudmfk9hcf0c64ng6bln0v; page-tab=1; d2mid=mKhLMgpRKTW1XqEUEUJAUMncZGJS0k; language=en"
    cookies = {cookie.split("=")[0]: cookie.split("=")[1] for cookie in cookie.split("; ")}
    response = session.get(LOUNGE_URL + endpoint, cookies=cookies)
    pprint(response.text)

def main():
    session = requests.Session()
    # Make session look like a browser
    session.headers.update({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)"})

    # matches = gather_matches(timeframe=60*10**9)
    matches = gather_local_matches(timeframe=60*10**9)

    for match in matches[0:1]:
        expected_value = match["expected_value"]

        if max(expected_value) <= 0.3:
         continue
    
        bet_team = most_profitable(match)

        match_time = time.mktime(time.strptime(str(match["time"]), "%Y-%m-%dT%H:%M:%S"))
        time_until = match_time - int(time.time())

        message = f"Match: {match['competitors'][0]} vs {match['competitors'][1]} (ID: {match['id']})\n" \
                  f"Pool Sizes: ${match['existing_value'][0]:0.2f} - ${match['existing_value'][1]:.2f}\n" \
                  f"Pool Odds: {match['lounge_odds'][0]:.2f} - {match['lounge_odds'][1]:.2f}\n" \
                  f"True Odds: {match['bovada_odds'][0]:.2f} - {match['bovada_odds'][1]:.2f}\n" \
                  f"Time: {timestamp_to_english(match_time)} ({seconds_to_readable(time_until)})\n" \
                  f"Bet on: {match['competitors'][bet_team]} with " \
                  f"${match['expected_value'][bet_team]:.2f} EV " \
                  f"({match['lounge_multiplier'][bet_team]:.2f}x)\n"

        # TODO: Automate bet placement
        place_bet(session, match, bet_team, 1)

        print(match['last_updated'])
        print(message)
        print()
        send_notification(message)


if __name__ == "__main__":
    main()