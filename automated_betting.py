# This script will check the status of upcoming matches through our API and send a notification if a high EV match is found.

import requests
import json
import time

from pprint import pprint
from src.models import UnifiedMatch, ModifiedMatch, Bet
from src.email import send_email


URL = "http://dserver:8000"
LOUNGE_URL = "https://csgolounge.com/"
LOCAL_DB_PATH = "matches.db"

MINIMUM_EV_THRESHOLD = 0.2
MINIMUM_POOL_THRESHOLD = 10

SECONDS_UNTIL_MATCH = 15

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

def gather_matches(timeframe=60):
    # Bets cannot be cancelled within 10 minutes of the match starting, so we want to place bets at the last possible moment to avoid the odds changing
    # We will check for matches that start within {timeframe} seconds from now and only consider those
    now = int(time.time())
    before = now + timeframe

    endpoint = f"/matches?before={before}&after={now}"
    response = requests.get(URL + endpoint)
    matches = json.loads(response.text)
    return matches


def send_notification(message):
    email_config = json.load(open("email_config.json", "r"))

    smtp_server = email_config["smtp_server"]
    smtp_port = email_config["smtp_port"]
    smtp_username = email_config["smtp_username"]
    smtp_password = email_config["smtp_password"]

    sender_email = email_config["sender_email"]
    receiver_email = email_config["receiver_email"]
    subject = "CSGO Betting Alert"

    send_email(
        sender_email,
        receiver_email,
        subject,
        message,
        smtp_server,
        smtp_port,
        smtp_username,
        smtp_password
    )


def is_high_ev(match: ModifiedMatch):
    exceeds_ev_threshold = match.expected_value[0] > MINIMUM_EV_THRESHOLD or match.expected_value[1] > MINIMUM_EV_THRESHOLD
    exceeds_pool_threshold = match.existing_value[0] > MINIMUM_POOL_THRESHOLD and match.existing_value[1] > MINIMUM_POOL_THRESHOLD
    high_ev = exceeds_ev_threshold and exceeds_pool_threshold
    side = int(match.expected_value[0] < match.expected_value[1])

    # Return both whether or not the match meets the high EV threshold and the side with the highest EV
    return (high_ev, side)


def determine_bet_size(match, side):
    # TODO: Determine the most profitable bet size using the Kelly Criterion (need a bigger bankroll to do this properly)
    bet_size = 1
    # Return the amount to bet
    return bet_size


def place_bet(match, side, amount):
    # Use our API to place a bet on a match
    # localhost:8000/bets

    url = f"{URL}/bets?match_id={match.lounge_id}&side={side+1}&amount={amount}"
    # print(url)

    response = requests.post(url)
    return response.json()


def cancel_bet(match_id):
    # Use our API to cancel a bet on a match
    # localhost:8000/bets

    url = f"{URL}/bets?match_id={match_id}"
    response = requests.delete(url)
    return response.json()


def get_bet(match_id):
    # Use our API to get the bet on a match
    # localhost:8000/bets

    url = f"{URL}/bets/{match_id}"
    response = requests.get(url)
    if 'error' in response.json():
        return None
    else:
        return Bet.from_JSON(response.json())


def main():
    matches_json = gather_matches(SECONDS_UNTIL_MATCH)
    matches = [UnifiedMatch.from_JSON(match) for match in matches_json]

    transactions = []

    for match in matches:
        tx = ""
        time.sleep(1)
        print(f"Checking match: {match.competitors[0]} vs {match.competitors[1]} {match.time}")

        # Check if a bet has already been placed on the match
        current_bet = get_bet(match.lounge_id)

        # Adjust the match to include the current bet (does nothing if current_bet is None)
        match = ModifiedMatch(unified_match=match, bet=current_bet)

        # Determine if the match is profitable
        profitable, side = is_high_ev(match)
        if not profitable and current_bet is None:
            continue

        elif not profitable and current_bet is not None:
            cancel_bet(match.lounge_id)
            print(f"Cancelled the existing bet on {match.competitors[current_bet.side - 1]}")

            tx += f"Cancelled the existing ${current_bet.amount} bet on {match.competitors[current_bet.side - 1]} as position is no longer profitable\n"
            transactions.append(tx)
            continue

        print(f"Found profitable bet on {match.competitors[side]} ({match.competitors[0]} vs {match.competitors[1]})")
        print(f"\tTime: {match.time}")
        print(f"\tEV: ${match.expected_value[0]:0.3f} vs ${match.expected_value[1]:0.3f}")
        print(f"\tCurrent Pools: ${match.existing_value[0]:0.3f} vs ${match.existing_value[1]:0.3f}")
        print(f"\tBovada Odds: {match.bovada_odds[0]*100:0.3f}% vs {match.bovada_odds[1]*100:0.3f}%")
        print(f"\tLounge Odds: {match.lounge_odds[0]*100:0.3f}% vs {match.lounge_odds[1]*100:0.3f}%")

        tx_identified_bet_message = f"Found profitable bet on {match.competitors[side]} ({match.competitors[0]} vs {match.competitors[1]})\n"
        tx_identified_bet_message += f"\tTime: {match.time}\n"
        tx_identified_bet_message += f"\tEV: ${match.expected_value[0]:0.3f} vs ${match.expected_value[1]:0.3f}\n"
        tx_identified_bet_message += f"\tCurrent Pools: ${match.existing_value[0]:0.3f} vs ${match.existing_value[1]:0.3f}\n"
        tx_identified_bet_message += f"\tBovada Odds: {match.bovada_odds[0]*100:0.3f}% vs {match.bovada_odds[1]*100:0.3f}%\n"
        tx_identified_bet_message += f"\tLounge Odds: {match.lounge_odds[0]*100:0.3f}% vs {match.lounge_odds[1]*100:0.3f}%\n"


        

        # Determine what most profitable bet size and side is
        amount = determine_bet_size(match, side)

        if current_bet is None:
            # Place a bet on the match
            place_bet(match, side, amount)
            print(f"Placed a bet on {match.competitors[side]} for ${amount}")

            tx += tx_identified_bet_message
            tx += f"Placed a bet on {match.competitors[side]} for ${amount}\n"
            transactions.append(tx)
            continue

        elif current_bet.side - 1 != side or current_bet.amount != amount:
            # Cancel the existing bet and place a new one
            cancel_bet(match.lounge_id)
            place_bet(match, side, amount)
            print(f"Cancelled the existing bet and placed a new one on {match.competitors[side]} for ${amount}")

            tx += tx_identified_bet_message
            tx += f"Placed a bet on {match.competitors[side]} for ${amount}\n"
            transactions.append(tx)
            continue

        else:
            print(f"Bet on {match.competitors[side]} for ${amount} is still valid")

    if len(transactions) > 0:
        with open("receipt.txt", "w+") as f:
            f.write("\n".join(transactions))
            print("Wrote transactions to receipt.txt")

        send_notification("\n".join(transactions))


if __name__ == "__main__":
    main()