import requests
from datetime import datetime, timezone, timedelta
import json
import os
from players import get_player_id

CACHE_FILE = "player_props_cache.json"

API_KEY = "42acb7ef1e5572fe4823ef94488a5c37"
SPORT = "basketball_nba"
MARKETS = "player_points,player_assists,player_rebounds,player_threes"
BOOKMAKERS = "draftkings"

#using cache so don't have to call credits a lot (ai helped me a lot on this one i dont know how to use it)
def save_cache(data):
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return None


def get_player_props(api_key=API_KEY, target_date=None, use_cache=True):
    
    if target_date is None:
        target_date = datetime.now().date()

    if use_cache:
        cached = load_cache()
        if cached and cached.get("date") == str(target_date):
            print("✅ Loaded player props from cache")
            return cached.get("props")

    events_url =  f"https://api.the-odds-api.com/v4/sports/{SPORT}/events/?apiKey={api_key}"
    response = requests.get(events_url)

    if response.status_code != 200:
        print("Error fetching events:", response.status_code, response.text)
        return None

    events_data = response.json()
    player_props_list = []

    #get player props

    for event in events_data:
        event_id = event["id"]

        # Convert UTC event time to local time
        utc_time = datetime.fromisoformat(event["commence_time"].replace("Z", "+00:00"))
        local_time = utc_time.astimezone()  # convert to local timezone

        if local_time.date() != target_date:
            continue  # skip events not on the target date

        props_url = (
            f"https://api.the-odds-api.com/v4/sports/{SPORT}/events/{event_id}/odds/"
            f"?apiKey={api_key}&bookmakers={BOOKMAKERS}&oddsFormat=american&markets={MARKETS}"
        )
        resp = requests.get(props_url)

        if resp.status_code != 200:
            print(f"Error fetching props for event {event_id}: {resp.status_code}")
            continue
        try:
            game_data = resp.json()
        except ValueError:
            print(f"No JSON returned for event {event_id}, skipping.")
            continue

        bookmakers = game_data.get("bookmakers", [])
        if not bookmakers:
            print(f"No bookmaker data for event {event_id}, skipping.")
            continue
        for bookmaker in bookmakers:
            for market in bookmaker.get("markets", []):
                stat_type = market.get("key")
                for outcome in market.get("outcomes", []):
                    player_props_list.append({
                            "player": outcome.get("description"),
                            "player_id": get_player_id(outcome.get("description")),
                            "stat": stat_type,
                            "line": outcome.get("point"),
                            "odds": outcome.get("price"),
                            "side": outcome.get("name"),
                            "game_time": local_time.strftime("%Y-%m-%d %H:%M:%S")
                        })

    print(f"✅ Collected {len(player_props_list)} lines for {target_date}.")
    if use_cache:
        save_cache({
            "date": str(target_date),
            "props": player_props_list
        })
    return player_props_list

        
# props = get_player_props(API_KEY)
# if props:
#     # Print first 5 to verify
#     for prop in props[:5]:
#         print(f"{prop['player']} | {prop['stat']} | {prop['side']} {prop['line']} ({prop['odds']})")


