from dataclasses import dataclass
from datetime import datetime

# Helper function to convert moneyline odds to implied probability
# Naive implementation, results in >100% probability, both sides should be normalized to correct this
def moneyline_to_probability(moneyline):
    if moneyline > 0:
        return 100 / (moneyline + 100)
    else:
        return -moneyline / (-moneyline + 100)
    

@dataclass
class BovadaMatch:
    time: int
    team1: str
    team2: str
    team1_moneyline: float
    team2_moneyline: float

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
    
    @staticmethod
    def from_event(event):
        return BovadaMatch(
            time=int(event["startTime"] / 1000),
            team1=event["competitors"][0]["name"],
            team2=event["competitors"][1]["name"],
            team1_moneyline=float(event["displayGroups"][0]["markets"][0]["outcomes"][0]["price"]["american"]),
            team2_moneyline=float(event["displayGroups"][0]["markets"][0]["outcomes"][1]["price"]["american"])
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
    "ALTERNATE aTTaX": "Alternate Attax"
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
    
    @staticmethod
    def from_dict(match_dict):
        id = int(match_dict["m_id"])
        time = int(match_dict["m_time"])
        status = int(match_dict["m_status"])

        # We arbitrarily choose to unify the names of the teams to the Bovada names
        team1 = lounge_to_bovada[match_dict["t1name"]] if match_dict["t1name"] in lounge_to_bovada else match_dict["t1name"]
        team2 = lounge_to_bovada[match_dict["t2name"]] if match_dict["t2name"] in lounge_to_bovada else match_dict["t2name"]

        # If no bets have been placed on the match, the sumbets key will not exist
        if "sumbets" not in match_dict:
            return LoungeMatch(id, time, status, team1, team2, 0, 0)
        
        # Convert the currencies to USD and calculate the total value of each team
        # TODO: Update the exchange rates periodically
        TO_USD = {"EUR": 1.09, "RUB": 0.011, "USD": 1}
        sumbets = match_dict["sumbets"]

        t1_value = 0
        t2_value = 0

        for currency in sumbets:
            if "1" not in sumbets[currency]:
                sumbets[currency]["1"] = 0

            if "2" not in sumbets[currency]:
                sumbets[currency]["2"] = 0

            t1_value += sumbets[currency]["1"] * TO_USD[currency]
            t2_value += sumbets[currency]["2"] * TO_USD[currency]

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
            "last_updated": self.last_updated
        }

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