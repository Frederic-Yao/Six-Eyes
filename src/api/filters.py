import pandas as pd


#filter a players games by conditions
def filter_games(df, home=None, opponent=None, min_minutes=None, last_n=None):
    filtered = df.copy() #stat with full dataframe

    filtered["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])
    filtered = filtered.sort_values("GAME_DATE")

    if home is True:
        filtered = filtered[filtered["MATCHUP"].str.contains("vs")]
    elif home is False:
        filtered = filtered[filtered["MATCHUP"].str.contains("@")]
    
    if opponent is not None:
        filtered = filtered[filtered["MATCHUP"].str[-3:] == opponent]
    
    if min_minutes is not None:#converting min column to float minutes if its string
        if filtered["MIN"].dtype == "object":#check if its a object type
            filtered["MIN_float"] = filtered["MIN"].apply(
                lambda x: int(x.split(":")[0]) + int(x.split(":")[1])/60
            )
            filtered = filtered[filtered["MIN_float"] >= min_minutes]
        else:
            filtered = filtered[filtered["MIN"] >= min_minutes]
            
    if last_n is not None:
        filtered = filtered.tail(last_n)
    
    return filtered