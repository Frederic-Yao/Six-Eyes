from nba_api.stats.endpoints import PlayerGameLog
from nba_api.stats.endpoints import TeamYearByYearStats
import numpy as np
from scipy.stats import norm
from players import get_player_log
from filters import filter_games
from helpers import get_team_stats

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
    logs = get_player_log(prop["player_id"], season="2025-26")

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
    season_avg = logs[prop["stat"]].mean()
    avg_15 = filtered_long[prop["stat"]].mean()
    avg_5 = filtered_short[prop["stat"]].mean()
    home_avg = home_games[prop["stat"]].mean()
    away_avg = away_games[prop["stat"]].mean()

    #projection based on last games only
    projection = (
        0.4 * season_avg +
        0.4 * avg_15 +
        0.2 * avg_5
        )
    
    #head to head factor
    if len(opponent_games) > 0:
        opponent_avg = opponent_games[prop["stat"]].mean() #stats against that team
        matchup_fact = opponent_avg / season_avg
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
        if prop["stat"] == "PTS":
            stat_def_fact = defense_fact
        elif prop["stat"] == "AST":
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

    #standard deviation computations
    long_std = filtered_long[prop["stat"]].std()
    short_std = filtered_short[prop["stat"]].std()
    combined_std = 0.5 * long_std + 0.5 * short_std
    combined_std = max(combined_std, 0.75)
    if len(opponent_games) > 1:
        opponent_std = opponent_games[prop["stat"]].std()
    else:
        opponent_std = combined_std
    final_std = 0.75 * combined_std + 0.25 * opponent_std

    #final projection
    p_over = float(round((1 - norm.cdf(line, loc=adjusted_projection, scale=final_std)) * 100, 2))
    p_under = float(round((100 - p_over), 2))
    print("Season avg:", season_avg)
    print("Avg 15:", avg_15)
    print("Avg 5:", avg_5)
    print("Final projection:", adjusted_projection)
    print("Std:", combined_std)
    print("Line:", line)
    print("P(over):", p_over)
    return(p_over, p_under) 

prop = {
    "player_id": "203084",   # Jokic
    "player_name": "Harrison Barnes",
    "stat": "AST",
    "line": 11.5
}
evaluate_prop_advanced(prop, home=True, opponent="NYK")

