import time

from dataclasses import dataclass
from datetime import datetime

# Helper function to convert moneyline odds to implied probability
# Naive implementation, results in >100% probability, both sides should be normalized to correct this
def moneyline_to_probability(moneyline):
    if moneyline > 0:
        return 100 / (moneyline + 100)
    else:
        return -moneyline / (-moneyline + 100)

# Helper function to parse moneyline odds from Bovada
# Sometimes the moneyline is EVEN, which is equivalent to +100
def parse_moneyline(moneyline):
        if moneyline == "EVEN":
            return 100
        
        return float(moneyline)

@dataclass
class BovadaMatch:
    time: int
    team1: str
    team2: str
    team1_moneyline: float
    team2_moneyline: float

    def title(self):
        return f"{self.team1} vs {self.team2} {datetime.fromtimestamp(self.time)}"

    @property
    def t1_odds(self):
        return moneyline_to_probability(self.team1_moneyline) / (moneyline_to_probability(self.team1_moneyline) + moneyline_to_probability(self.team2_moneyline))
    
    @property
    def t2_odds(self):
        return moneyline_to_probability(self.team2_moneyline) / (moneyline_to_probability(self.team1_moneyline) + moneyline_to_probability(self.team2_moneyline))
    
    @property
    def t1_multiplier(self):
        return 1 / self.t1_odds if self.t1_odds != 0 else 0
    
    @property
    def t2_multiplier(self):
        return 1 / self.t2_odds if self.t2_odds != 0 else 0
    
    def reversed(self):
        return BovadaMatch(
            time=self.time,
            team1=self.team2,
            team2=self.team1,
            team1_moneyline=self.team2_moneyline,
            team2_moneyline=self.team1_moneyline
        )
    
    def to_JSON(self):
        return {
            "time": self.time,
            "team1": self.team1,
            "team2": self.team2,
            "team1_moneyline": self.team1_moneyline,
            "team2_moneyline": self.team2_moneyline
        }
    
    @staticmethod
    def from_JSON(json):
        return BovadaMatch(
            time=json["time"],
            team1=json["team1"],
            team2=json["team2"],
            team1_moneyline=json["team1_moneyline"],
            team2_moneyline=json["team2_moneyline"]
        )
      
    @staticmethod
    def from_event(event):
        team1 = event["competitors"][0]["name"]
        team2 = event["competitors"][1]["name"]
        team1, team2 = team1.strip(), team2.strip()

        return BovadaMatch(
            time=int(event["startTime"] / 1000),
            team1=team1,
            team2=team2,
            team1_moneyline=parse_moneyline(event["displayGroups"][0]["markets"][0]["outcomes"][0]["price"]["american"]),
            team2_moneyline=parse_moneyline(event["displayGroups"][0]["markets"][0]["outcomes"][1]["price"]["american"])
        )


# Helper function to convert CSGOLounge team names to Bovada team names
lounge_to_bovada = {
    "Astralis": "Astralis",
    "BIG": "BIG",
    "G2": "G2",
    "Liquid": "Team Liquid",
    "Cloud9": "Cloud9",
    "Rebels": "Rebels Gaming",
    "Eternal Fire": "Eternal Fire",
    "BB": "BB Team",
    "Ence": "Ence",
    "Heroic": "Heroic",
    "FURIA": "FURIA Esports",
    "TheMongolz": "TheMongolz",
    "Spirit": "Team Spirit",
    "Apeks": "Apeks",
    "GamerLegion": "GamerLegion",
    "M80": "M80",
    "Rooster": "Rooster",
    "VP": "Virtus.pro",
    "Alliance": "Alliance",
    "Spirit Academy": "Spirit Academy",
    "Sangal": "Sangal Esports",
    "ECSTATIC": "ECSTATIC",
    "Into the Breach": "Into The Breach",
    "BIG Academy": "BIG OMEN Academy",
    "BLEED": "Bleed",
    "Metizport": "Metizport",
    "Preasy": "Preasy",
    "Entropiq": "Entropiq",
    "Sprout": "Sprout",
    "ALTERNATE aTTaX": "Alternate Attax",
    "BESTIA": "Bestia",
    "Imperial (Brazil)": "Imperial Esports",
    "Na'Vi": "Natus Vincere",
    "Wildcard": "Wildcard Gaming",
    "coL": "Complexity",
    "mousesports": "Mouz",
    "mibr": "MIBR",
    "Sinners (CZ)": "SinnerS",
    'ex-Anonymo': 'ex-Anonymo Esports',
}


@dataclass
class LoungeMatch:
    id: int
    time: int
    status: int
    team1: str
    team2: str
    t1_value: float
    t2_value: float

    def title(self):
        return f"{self.team1} vs {self.team2} {datetime.fromtimestamp(self.time)}"

    @property
    def total_value(self):
        return self.t1_value + self.t2_value
    
    @property
    def t1_odds(self):
        return self.t1_value / self.total_value if self.total_value != 0 else 0
    
    @property
    def t2_odds(self):
        return self.t2_value / self.total_value if self.total_value != 0 else 0
    
    @property
    def t1_multiplier(self):
        return 1 / self.t1_odds if self.t1_odds != 0 else 0
    
    @property
    def t2_multiplier(self):
        return 1 / self.t2_odds if self.t2_odds != 0 else 0
    
    def to_JSON(self):
        return {
            "id": self.id,
            "time": self.time,
            "status": self.status,
            "team1": self.team1,
            "team2": self.team2,
            "t1_value": self.t1_value,
            "t2_value": self.t2_value
        }
    
    @staticmethod
    def from_JSON(json):
        return LoungeMatch(
            id=json["id"],
            time=json["time"],
            status=json["status"],
            team1=json["team1"],
            team2=json["team2"],
            t1_value=json["t1_value"],
            t2_value=json["t2_value"]
        )
    
    @staticmethod
    def from_dict(match_dict):
        id = int(match_dict["m_id"])
        time = int(match_dict["m_time"])
        status = int(match_dict["m_status"])

        # We arbitrarily choose to unify the names of the teams to the Bovada names
        team1 = lounge_to_bovada[match_dict["t1name"]] if match_dict["t1name"] in lounge_to_bovada else match_dict["t1name"]
        team2 = lounge_to_bovada[match_dict["t2name"]] if match_dict["t2name"] in lounge_to_bovada else match_dict["t2name"]
        team1, team2 = team1.strip(), team2.strip()

        # If no bets have been placed on the match, the sumbets key will not exist
        if "sumbets" not in match_dict:
            return LoungeMatch(id, time, status, team1, team2, 0, 0)
        
        # Convert the currencies to USD and calculate the total value of each team
        # TODO: Update the exchange rates periodically
        sumbets = match_dict["sumbets"]

        pool_sizes = {'USD': (0, 0),
                  'EUR': (0, 0),
                  'RUB': (0, 0),}
        
        exchange_rates = {'USD': 1,
                          'EUR': 1.08,
                          'RUB': 0.011}
        
        for currency in sumbets.keys():
            if '1' not in sumbets[currency]:
                sumbets[currency]["1"] = 0
            if '2' not in sumbets[currency]:
                sumbets[currency]["2"] = 0

            pool_sizes[currency] = (sumbets[currency]["1"]*exchange_rates[currency], sumbets[currency]["2"]*exchange_rates[currency])

        sort = sorted(pool_sizes.values(), key=lambda x: x[0] + x[1], reverse=True)
        
        t1_value = sort[0][0]
        t2_value = sort[0][1]

        return LoungeMatch(id, time, status, team1, team2, t1_value / 100, t2_value / 100)
    
@dataclass
class UnifiedMatch:
    _bovada_match: BovadaMatch
    _lounge_match: LoungeMatch
    last_updated: int = 0

    @property
    def time(self):
        # We choose to use the CSGOLounge time as the time of the match since that is where the match is being bet on
        return datetime.fromtimestamp(self._lounge_match.time)
    
    @property
    def competitors(self):
        return self._lounge_match.team1, self._lounge_match.team2
    
    @property
    def status(self):
        return self._lounge_match.status
    
    @property
    def bovada_odds(self):
        return self._bovada_match.t1_odds, self._bovada_match.t2_odds
    
    @property
    def lounge_id(self):
        return self._lounge_match.id
    
    @property
    def lounge_odds(self):
        return self._lounge_match.t1_odds, self._lounge_match.t2_odds
    
    @property
    def lounge_multiplier(self):
        return self._lounge_match.t1_multiplier, self._lounge_match.t2_multiplier
    
    @property
    def existing_value(self):
        return self._lounge_match.t1_value, self._lounge_match.t2_value
    
    @property
    def expected_value(self):
        t1_ev = self.bovada_odds[0] * self.lounge_multiplier[0] - 1
        t2_ev = self.bovada_odds[1] * self.lounge_multiplier[1] - 1

        return t1_ev, t2_ev
    
    def pprint(self):
        print(f"{self.competitors[0]} vs {self.competitors[1]} @ {self.time} (ID: {self.lounge_id})")
        print(f"    Existing value: ${self.existing_value[0]:0.2f} vs ${self.existing_value[1]:0.2f}")
        print(f"    (Lounge) {self.lounge_odds[0] * 100:0.2f}% vs {self.lounge_odds[1] * 100:0.2f}%")
        print(f"    (Bovada) {self.bovada_odds[0] * 100:0.2f}% vs {self.bovada_odds[1] * 100:0.2f}%")
        print(f"    Payout: {self.lounge_multiplier[0]:0.2f}x vs {self.lounge_multiplier[1]:0.2f}x")
        print(f"    Expected Value: ${self.expected_value[0]:0.2f} vs ${self.expected_value[1]:0.2f}")

    def to_JSON(self):
        # This is slightly different from the serialize method, serialize keeps data in an easily recoverable format
        # This method is used to send data from the server to the client, so it is formatted in a way that is easy to display

        return {
            "id": self.lounge_id,
            "time": self.time,
            "competitors": self.competitors,
            "status": self.status,
            "existing_value": self.existing_value,
            "lounge_odds": self.lounge_odds,
            "bovada_odds": self.bovada_odds,
            "lounge_multiplier": self.lounge_multiplier,
            "expected_value": self.expected_value,
            "last_updated": self.last_updated,
            "lounge_match": self._lounge_match.to_JSON(),
            "bovada_match": self._bovada_match.to_JSON()
        }
    
    @staticmethod
    def from_JSON(json):
        return UnifiedMatch(
            BovadaMatch.from_JSON(json["bovada_match"]),
            LoungeMatch.from_JSON(json["lounge_match"]),
            last_updated=json["last_updated"]
        )

    def serialize(self):
        return {
            "lounge_id": int(self._lounge_match.id),
            "lounge_time": int(self._lounge_match.time),
            "lounge_status": self._lounge_match.status,
            "lounge_team1": self._lounge_match.team1,
            "lounge_team2": self._lounge_match.team2,
            "lounge_t1_value": self._lounge_match.t1_value,
            "lounge_t2_value": self._lounge_match.t2_value,
            "bovada_time": int(self._bovada_match.time),
            "bovada_team1": self._bovada_match.team1,
            "bovada_team2": self._bovada_match.team2,
            "bovada_t1_moneyline": self._bovada_match.team1_moneyline,
            "bovada_t2_moneyline": self._bovada_match.team2_moneyline,
            "last_updated": self.last_updated
        }
    
    @staticmethod
    def deserialize(serialized):
        return UnifiedMatch(
            BovadaMatch(
                time=serialized["bovada_time"],
                team1=serialized["bovada_team1"],
                team2=serialized["bovada_team2"],
                team1_moneyline=serialized["bovada_t1_moneyline"],
                team2_moneyline=serialized["bovada_t2_moneyline"]
            ),
            LoungeMatch(
                id=serialized["lounge_id"],
                time=serialized["lounge_time"],
                status=serialized["lounge_status"],
                team1=serialized["lounge_team1"],
                team2=serialized["lounge_team2"],
                t1_value=serialized["lounge_t1_value"],
                t2_value=serialized["lounge_t2_value"]
            ),
            last_updated=serialized["last_updated"]
        )
    
class Bet:
    def __init__(self, match_id:int , side: int, amount: float, time_placed:int = None):
        self.match_id = match_id
        self.side = side
        self.amount = amount
        self.time_placed = time_placed if time_placed is not None else int(time.time())

    def to_JSON(self):
        return {
            "match_id": self.match_id,
            "side": self.side,
            "amount": self.amount,
            "time_placed": self.time_placed
        }
    
    @staticmethod
    def from_JSON(json):
        return Bet(
            match_id=json["match_id"],
            side=json["side"],
            amount=json["amount"],
            time_placed=json["time_placed"]
        )


# A modified match is a unified match with a bet placed on it, hence the value of of one of the teams is reduced by the amount of the bet
class ModifiedMatch:
    def __init__(self, unified_match: UnifiedMatch, bet: Bet = None):
        self.unified_match = unified_match
        self.bet = bet if bet is not None else Bet(0, 0, 0)

        # Adjust the value of the team that the bet was placed on
        if self.bet.side == 0:
            self.unified_match._lounge_match.t1_value -= self.bet.amount
        else:
            self.unified_match._lounge_match.t2_value -= self.bet.amount
    
    @property
    def time(self):
        return self.unified_match.time
    
    @property
    def competitors(self):
        return self.unified_match.competitors
    
    @property
    def status(self):
        return self.unified_match.status
    
    @property
    def bovada_odds(self):
        return self.unified_match.bovada_odds
    
    @property
    def lounge_id(self):
        return self.unified_match.lounge_id
    
    @property
    def lounge_odds(self):
        return self.unified_match.lounge_odds
    
    @property
    def lounge_multiplier(self):
        return self.unified_match.lounge_multiplier
    
    @property
    def existing_value(self):
        return self.unified_match.existing_value
    
    @property
    def expected_value(self):
        return self.unified_match.expected_value

    