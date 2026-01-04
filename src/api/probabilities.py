from nba_api.stats.endpoints import PlayerGameLog, teamgamelog, TeamYearByYearStats
import numpy as np
from scipy.stats import norm
from players import get_player_log
from filters import filter_games
from helpers import get_team_stats, get_team_id, american_to_prob
import pandas as pd

TEAM_ABBR_TO_NAME = {
    "ATL": "Atlanta Hawks",
    "BOS": "Boston Celtics",
    "BKN": "Brooklyn Nets",
    "CHA": "Charlotte Hornets",
    "CHI": "Chicago Bulls",
    "CLE": "Cleveland Cavaliers",
    "DAL": "Dallas Mavericks",
    "DEN": "Denver Nuggets",
    "DET": "Detroit Pistons",
    "GSW": "Golden State Warriors",
    "HOU": "Houston Rockets",
    "IND": "Indiana Pacers",
    "LAC": "LA Clippers",
    "LAL": "L.A. Lakers",
    "MEM": "Memphis Grizzlies",
    "MIA": "Miami Heat",
    "MIL": "Milwaukee Bucks",
    "MIN": "Minnesota Timberwolves",
    "NOP": "New Orleans Pelicans",
    "NYK": "New York Knicks",
    "OKC": "Oklahoma City Thunder",
    "ORL": "Orlando Magic",
    "PHI": "Philadelphia 76ers",
    "PHX": "Phoenix Suns",
    "POR": "Portland Trail Blazers",
    "SAC": "Sacramento Kings",
    "SAS": "San Antonio Spurs",
    "TOR": "Toronto Raptors",
    "UTA": "Utah Jazz",
    "WAS": "Washington Wizards"

}
#because NBA_API and the odds api format the props differently
STAT_MAP = {
    "player_points": "PTS",
    "player_assists": "AST",
    "player_rebounds": "REB",
    "player_threes": "FG3M"
}

# GLOBAL CACHE
b2b_cache = {}
PLAYER_LOG_CACHE = {}

def is_b2b(logs):
    """
    returns true of the team logs shows a back to back game
    """
    if len(logs) < 2:
        return False
    games = logs.sort_values("GAME_DATE", ascending=False).copy()
    games["GAME_DATE"] = pd.to_datetime(games["GAME_DATE"], format="%b %d, %Y")

    current_game = games.iloc[0]["GAME_DATE"]
    last_game = games.iloc[1]["GAME_DATE"]

    return (current_game - last_game).days == 1

def get_b2b(team_id, logs):
    """
    Returns True if the team (team_id) is on a back-to-back for the given game_date.
    Uses a global cache to avoid repeated computation.
    """
    # Use team_id + latest game date as cache key
    logs_sorted = logs.sort_values("GAME_DATE", ascending=False)
    latest_game_date = pd.to_datetime(logs_sorted.iloc[0]["GAME_DATE"])
    key = (team_id, latest_game_date)

    # Return cached value if exists
    if key in b2b_cache:
        return b2b_cache[key]

    # Compute B2B
    b2b = is_b2b(logs)
    b2b_cache[key] = b2b
    return b2b

def evaluate_prop_advanced(
        prop, last_n_short=5, last_n_long=15, min_minutes=20,
        home=None, opponent=None, team_def_factor=1.0, zone_factor=1.0
        ):
    """
    Evaluating a prop using
    - last 5 and 15 games
    - home and away
    - optional head-to-head
    - team defense and zone adjustments
    """
    
    #load cache if possible
    player_id = prop["player_id"] 
    if player_id not in PLAYER_LOG_CACHE:
        PLAYER_LOG_CACHE[player_id] = get_player_log(player_id, season="2025-26")

    logs = PLAYER_LOG_CACHE[player_id]
    if logs is None or logs.empty:
        print(f"⚠️ Skipping {player_id} - No data found.")
        return None # This tells main.py to skip this prop

    #filtering games to fetch different stats
    filtered_long = filter_games(logs, last_n=last_n_long, min_minutes=18, home=None)
    filtered_short = filter_games(logs, last_n=last_n_short, min_minutes=18, home=None)
    home_games = filter_games(logs, home=True)
    away_games = filter_games(logs, home=False)
    opponent_games = filter_games(logs, opponent=opponent)

    #safety check for enough games
    if len(filtered_long) < 5:
        return None
    
    line = prop["line"] #the line

    #historical info, and other factors for weighted projection
    stat_col = STAT_MAP.get(prop["stat"])
    if stat_col not in logs.columns:
        print(f"Stat {prop["stat"]} not found for {prop["player"]}, skipping.")
        return None
    season_avg = logs[stat_col].mean()
    avg_15 = filtered_long[stat_col].mean()
    avg_5 = filtered_short[stat_col].mean()

    season_min = logs["MIN"].mean() #average minutes
    last15_min = filtered_long["MIN"].mean()
    last5_min = filtered_short["MIN"].mean()
    if np.isnan(last5_min):
        last5_min = season_min
    elif last5_min < 15:
        last5_min = last15_min
    expected_minutes = 0.65 * last5_min + 0.35 * season_min #cap or clip the swing if necessary

    home_avg = home_games[stat_col].mean()
    away_avg = away_games[stat_col].mean()

    #b2b y/n
    if opponent:
        OPPONENT_TEAM_ID = get_team_id(opponent)
        opponent_logs = teamgamelog.TeamGameLog(
            team_id=OPPONENT_TEAM_ID,
            season="2025-26"
        ).get_data_frames()[0]

        opponent_b2b = get_b2b(OPPONENT_TEAM_ID, opponent_logs)
    else:
        OPPONENT_TEAM_ID = None
        opponent_logs = None
        opponent_b2b = False  # assume not b2b if unknown

    player_b2b = is_b2b(logs)


    #rate stats
    last_5_stat_rate = avg_5 / last5_min
    last_15_stat_rate = avg_15 / last15_min
    season_rate = season_avg / season_min
    base_rate = ( #base rate expected
        0.3 * season_rate + 
        0.4 * last_15_stat_rate + 
        0.3 * last_5_stat_rate
    )

    #back to back factors
    minutes_fact = 1.0 #minutes decrease if players play on back to back
    efficiency_fact = 1.0 #altered if b2b or opopnent b2b

    if player_b2b:
        minutes_fact *= 0.95
    
    expected_minutes *= minutes_fact
    
    efficiency_fact *= 1.0
    if player_b2b:
        efficiency_fact *= 0.95
    
    if opponent_b2b:
        efficiency_fact *= 1.045
    
    base_rate *= efficiency_fact

    #projection based on expected minutes and rates
    projection = expected_minutes * base_rate

    #head to head factor
    if len(opponent_games) > 0:
        opponent_avg = opponent_games[stat_col].mean() #stats against that team
        matchup_fact = opponent_avg / season_avg if season_avg > 0 else 1.0
    else:
        matchup_fact = 1.0
    matchup_fact = np.clip(matchup_fact, 0.9, 1.1)
    projection *= matchup_fact

    #opponent defensive rating and pace
    if opponent:
        #Change to the abbreviation
        if opponent in TEAM_ABBR_TO_NAME:
            opponent_name = TEAM_ABBR_TO_NAME[opponent]
        else:
            opponent_name = opponent

        team_stats = get_team_stats(season="2026")
        league_avg_def = team_stats["DRtg"].mean()
        league_avg_pace = team_stats["Pace"].mean()

        #getting defensive ratings and pace
        opponent_row = team_stats[team_stats["Team"] == opponent_name]
        if opponent_row.empty:
            raise ValueError(f"Opponent '{opponent}' not found in team stats")
        opponent_def = opponent_row["DRtg"].values[0]
        opponent_pace = opponent_row["Pace"].values[0]
        
        #calculating factors
        defense_fact = league_avg_def / opponent_def
        pace_fact = opponent_pace / league_avg_pace
        stat_def_fact = 1.0
        if prop[stat_col] == "PTS":
            stat_def_fact = defense_fact
        elif prop[stat_col] == "AST":
            stat_def_fact = 1 + (defense_fact - 1) * 0.5
        stat_def_fact = np.clip(stat_def_fact, 0.9, 1.1)
        pace_fact = np.clip(pace_fact, 0.95, 1.05)

        #updating projection
        projection *= stat_def_fact
        projection *= pace_fact

    #compute home/away factors and reduce sample noice if the sample too small
    n_home = len(home_games)
    n_away = len(away_games)

    if n_home < 5:
        home_fact = 0.5 * (home_avg / season_avg) + 0.5 * 1.0
    else:
        home_fact = home_avg / season_avg
    home_fact = np.clip(home_fact, 0.9, 1.1) #set bounds

    if n_away < 5:
        away_fact = 0.5 * (away_avg / season_avg) + 0.5 * 1.0
    
    else:
        away_fact = away_avg / season_avg
    away_fact = np.clip(away_fact, 0.9, 1.1)

    #adjust according to factor
    if home is True:
        adjusted_projection = projection * (1 + 0.5 * (home_fact - 1))
    elif home is False:
        adjusted_projection = projection * (1 + 0.5 * (away_fact - 1))
    else:
        adjusted_projection = projection

    #rate stds 
    rate_short = filtered_short[stat_col] / filtered_short["MIN"]
    rate_long = filtered_long[stat_col] / filtered_long["MIN"]
    rate_std = 0.5 * rate_short.std() + 0.5 * rate_long.std()
    minutes_scaled_std = rate_std * expected_minutes 

    #std based on averages and opponents
    long_std = filtered_long[stat_col].std() 
    short_std = filtered_short[stat_col].std()
    combined_std = 0.5 * long_std + 0.5 * short_std
    combined_std = max(combined_std, 0.75) 

    if len(opponent_games) > 1:
        opponent_std = opponent_games[stat_col].std()
    else:
        opponent_std = combined_std
    
    #blend both
    final_std = combined_std * 0.6 + minutes_scaled_std *0.4
    final_std = 0.75 * final_std + 0.25 * opponent_std

    #stds with b2b
    std_multiplier = 1.0
    if player_b2b or opponent_b2b:
        std_multiplier *= 1.05

    if player_b2b and opponent_b2b:
        std_multiplier *= 1.03

    final_std *= std_multiplier
    final_std = max(final_std, 0.5) #clamp it so norm.cdf gives more stable results

    #final projection
    p_over = float(round((1 - norm.cdf(line, loc=adjusted_projection, scale=final_std)) * 100, 2))
    p_under = float(round((100 - p_over), 2))
    print("Season avg:", round(season_avg, 2))
    print("Avg 15:", round(avg_15, 2))
    print("Avg 5:", round(avg_5, 2))
    print("Final projection:", round(adjusted_projection, 2))
    print("Std:", round(final_std, 2))
    print("Line:", line)
    print("P(over):", p_over)

    return(p_over, p_under) 


prop = {
    "player_id": 2544,
    "player": "Lebron",
    "stat": "PTS",
    "line": 24.5,
    "over_odds": -110,
    "under_odds": -110,
    "opponent": "MIL",
    "home": True
}

evaluate_prop_advanced(prop, home=False, opponent="CHI")

