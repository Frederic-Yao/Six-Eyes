from nba_api.stats.endpoints import PlayerGameLog
from nba_api.stats.static import players

def get_player_log(player_id, season): #get player's game logs for a season in a panda Data frame
    logs = PlayerGameLog(player_id=player_id, season=season).get_data_frames()[0]
    return logs

player_list = players.find_players_by_full_name("harrison barnes")
print(player_list)


