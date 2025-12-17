from basketball_reference_scraper import players
import pandas as pd

#get all the player stats for the 2024-2025 NBA season
df = players.get_stats(2025)