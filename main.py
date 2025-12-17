from players import get_player_log
from filters import filter_games
from probabilities import stat_over_prob, stat_line_prob, evaluate_prop


all_players = [
    {"id": "203999", "name": "Nikola Jokic"},
    {"id": "201935", "name": "James Harden"},
    {"id": "2544", "name": "LeBron James"}
]
stats = ["PTS", "REB", "AST"]
dummy_lines = {
    "Nikola Jokic": {"PTS": 26.5, "REB": 12.5, "AST": 8.5},
    "James Harden": {"PTS": 28.5, "REB": 5.5, "AST": 7.5},
    "LeBron James": {"PTS": 27.5, "REB": 7.5, "AST": 7.5}
}

all_props = []
for player in all_players:
    for stat in stats:
        line = dummy_lines[player["name"]][stat]
        prop = {
            "player_id": player["id"],
            "player_name": player["name"],
            "stat": stat,
            "line": line
            }
        all_props.append(prop)

all_results = []

for prop in all_props:
    result = evaluate_prop(prop)
    if result:
        all_results.append(result)
for r in all_results:
    print(f"{r["player_name"]} {r["stat"]} over {r["line"]}: {r["p_over"]}%")