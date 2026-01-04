import pandas as pd
from nba_api.stats.static import teams

def get_team_stats(season="2026"):
    #URL for season team stats
    url = f"https://www.basketball-reference.com/leagues/NBA_2026.html"

    #read all tables from the page
    tables = pd.read_html(url)

    #team stats table
    team_stats = tables[10]

    #flatten multi index into single strings instead of tuples
    team_stats.columns = [f"{i}_{j}".strip("_") for i,j in team_stats.columns]

    team_stats = team_stats.rename(columns={ #rename the columns because they were whack
        'Unnamed: 1_level_0_Team': "Team",
        'Unnamed: 11_level_0_DRtg': "DRtg",
        'Unnamed: 13_level_0_Pace': "Pace"
    })

    team_stats = team_stats[["Team", "DRtg", "Pace"]]
    team_stats["DRtg"] = pd.to_numeric(team_stats["DRtg"])
    team_stats["Pace"] = pd.to_numeric(team_stats["Pace"])

    return team_stats

# print(get_team_stats(season="2026"))

def get_team_id(abbreviation):
    all_teams = teams.get_teams()
    team = [t for t in all_teams if t['abbreviation'] == abbreviation.upper()]
    if team:
        return team[0]['id']
    else:
        raise ValueError(f"Team abbreviation '{abbreviation}' not found")

def american_to_prob(odds):
    if odds < 0:
        return(-odds) / ((-odds) + 100)
    else:
        return 100 / (odds + 100)