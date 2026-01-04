from filters import filter_games
from probabilities import get_b2b, is_b2b, evaluate_prop_advanced
from get_odds import get_player_props
from helpers import american_to_prob

# GLOBAL CACHE
b2b_cache = {}
PLAYER_LOG_CACHE = {}

API_KEY = "42acb7ef1e5572fe4823ef94488a5c37"

#calling the function
props = get_player_props(API_KEY)

if not props:
    print("No props available.")
    exit()

evaluated_props = []

for prop in props:
    model_prob = evaluate_prop_advanced(prop)
    if model_prob is None:
        continue
    implied_prob = american_to_prob(prop["odds"])
    over_prob, under_prob = model_prob #since evaluate_prop_advanced returns a tuple

    if prop["side"] == "Over":
        edge = over_prob - implied_prob
    else:
        edge = under_prob - implied_prob

    model_side_prob = ( #taking one of the two from the tuple for final output
    over_prob if prop["side"] == "Over" else under_prob
)
    evaluated_props.append({
        **prop,
        "model_prop": round(model_side_prob, 3),
        "implied_prob": round(implied_prob, 3),
        "edge": round(edge, 3)
    })

evaluated_props.sort(key=lambda x: x["edge"], reverse=True)
for p in evaluated_props[:5]:
    print(
        f"{p['player']} | {p['stat']} | {p['side']} {p['line']} "
        f"({p['odds']}) | Edge: {p['edge']}"
    )