from nba_api.stats.endpoints import PlayerGameLog
from nba_api.stats.static import players
import unicodedata
import re
import time
import random
import requests

session = requests.Session()

def get_player_log(player_id, season, retries=5): #get player's game logs for a season in a panda Data frame
    
    #defining headers to mimic a real browser so we do not get throttled
    custom_headers = {
        'Host': 'stats.nba.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.nba.com/', # Must have the trailing slash
        'Origin': 'https://www.nba.com',
        'Connection': 'keep-alive',
    }
    for attempt in range(1, retries + 1):
        try:
            #Warm up the session by visiting the home page first (Stealth move)
            session.get("https://www.nba.com", headers=custom_headers, timeout=15)
            time.sleep(random.uniform(1.5, 3)) #delay to avoid getting flagged
        
            log_request = PlayerGameLog(
                player_id=player_id, 
                season=season, 
                headers=custom_headers, 
                timeout=60,
                proxy=None
            )
            df = log_request.get_data_frames()[0]
            # Anti-ban sleep: Pause between every player request
            time.sleep(random.uniform(1.5, 3.0)) 
            return df
            
        except Exception as e:
            wait_time = attempt * 2
            print(f"❌ Failed to fetch {player_id}: {e}")
            time.sleep(wait_time)

    print(f"❌ Failed to fetch logs for player {player_id} after {retries} attempts.")
    return None

def get_player_id(name):
    #removing accents
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    #removing dots
    name = name.replace(".", "")
    #collapse spaces
    name = re.sub(r"\s+", " ", name).strip()

    player = players.find_players_by_full_name(name)

    if not player:
        print(f"No player found with name: {name}")
        return None
    
    return player[0]["id"]

# player_list = get_player_id("R.J. barrett")
# print(player_list)


