import time
import requests
import json

from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.database import Database
from src.auth import CSGOLoungeAuth
from src.models import Bet

config = json.load(open("api_config.json", "r"))

DB_PATH = config["db_path"]
STEAM_COOKIES_PATH = config["cookies_path"]
AUTHENTICATION_SAVE_FILE = config["authentication"]

db = Database(DB_PATH, auto_connect=False, auto_init=False)
auth = CSGOLoungeAuth(steam_cookies_path=STEAM_COOKIES_PATH,
                           save_file=AUTHENTICATION_SAVE_FILE,
                           headless=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database
    db.connect()
    db.init()
    yield

    # Close the database
    db.close()

app = FastAPI(lifespan=lifespan)


@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.get("/matches")
async def read_matches(limit: int = 100, before: int | None = None, after: int | None = None, status: int | None = None):
    # TODO: Add support for querying by team or teams

    if before is not None and after is not None:
        return [match.to_JSON() for match in db.get_matches_between_times(after, before)][0:limit]
    elif before is not None:
        return [match.to_JSON() for match in db.get_matches_before_time(before)][0:limit]
    elif after is not None:
        return [match.to_JSON() for match in db.get_matches_after_time(after)][0:limit]
    elif status is not None:
        return [match.to_JSON() for match in db.get_matches_by_status(status)][0:limit]
    else:
        return [match.to_JSON() for match in db.get_matches()][0:limit]
    
@app.get("/matches/{match_id}")
async def read_match(match_id: int):
    match = db.get_match_by_id(match_id)
    if match is None:
        return {"error": "match not found"}
    else:
        return match.to_JSON()
    
@app.get("/matches/{match_id}/historical")
async def read_matches_historical(match_id: int, limit: int = 100, after: int | None = None, before: int | None = None):
    start = time.time()
    matches = db.get_historical_matches_by_id(match_id)
    
    print(f"Time to get historical matches: {time.time() - start}")
    if not matches:
        return {"error": "match not found"}
    
    else:
        start = time.time()
        
        response = [match.to_JSON() for match in matches]
        response = response[-1:0:-len(response)//limit]
        print(f"Time to convert to JSON: {time.time() - start}")
        # return {y: [{x: [n for n in range(0, 10)]} for x in range(0, 10)] for y in range(0, 10)}
        return response
    
@app.get("/bets")
async def read_bets(limit: int = 100):
    bets = db.get_bets()
    print(bets)
    return [bet.to_JSON() for bet in bets][0:limit]

@app.get("/bets/{bet_id}")
async def read_bet(bet_id: int):
    bet = db.get_bet_by_match_id(bet_id)
    if bet is None:
        return {"error": "bet not found"}
    else:
        return bet.to_JSON()
    
# Place a bet on a match with:
# match_id: int, side: int, amount: float
# side: 0 for team1, 1 for team2
@app.post("/bets")
async def place_bet(match_id: int, side: int, amount: float):
    match = db.get_match_by_id(match_id)
    if match is None:
        return {"error": "match not found"}
    if match.time.timestamp() < time.time():
        return {"error": "match has already started"}
    
    bet = None
    for i in range(3):
        try:
            lounge_session = auth.get_session()
            token = lounge_session["token"]
            cookies = lounge_session["cookie"]

            url = f"https://csgolounge.com/index/placebet/{match_id}/{side}/{amount}/{token}/"
            print(url)
            response = requests.get(url, cookies=cookies)
            if not response.json()["success"]: # if the bet fails, this will throw a JSONDecodeError
                if response.json()["error"] == 'An error occurred (closed). Please reload the page and try again.':
                    return {"error": "Match has already started"}
                elif response.json()["error"] == 'Error: You don’t have enough money on your account':
                    return {"error": "Insufficient funds"}
                else:
                    return {"error": response.json()["error"]}

            bet = Bet(
                    match_id=match_id,
                    side=side,
                    amount=amount,
                    time_placed=time.time()
                )
            break

        except Exception as e:
            print(f"Error placing bet: {e}, retrying {3 - i} more times")
            auth.reauthenticate()

    if bet is None:
        return {"error": "Bet failed"}
    
    try:
        db.insert_bet(bet)
    except Exception as e:
        print(f"Error inserting bet into database: {e}")
    
    return bet.to_JSON()

# Cancel a bet with:
# match_id: int
# TODO: Change this to use /bets/{bet_id} instead
@app.delete("/bets")
async def cancel_bet(match_id: int):
    match = db.get_match_by_id(match_id)
    if match is not None and match.time.timestamp() < time.time():
        return {"error": "match has already started"}
    
    attempts = 0
    for i in range(3):
        attempts = i
        try:
            lounge_session = auth.get_session()
            token = lounge_session["token"]
            cookies = lounge_session["cookie"]

            url = f"https://csgolounge.com/index/cancelbet/{match_id}/{token}/"
            response = requests.post(url, cookies=cookies)
            if not response.json()["success"]: # If authentication fails, this will throw a JSONDecodeError
                if response.json()["error"] == 'Error: Event not found. Please reload the page and try again.':
                    return {"error": "No bet found"}
                return {"error": response.json()["error"], "attempts": i}
            
            break

        except Exception as e:
            print(f"Error canceling bet: {e}, retrying {3 - i} more times")
            auth.reauthenticate()

    db.delete_bet_by_match_id(match_id)
    return {"success": True, "attempts": attempts}

