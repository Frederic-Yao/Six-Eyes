import requests
from dotenv import load_dotenv
import os

#loading API key from .env file
load_dotenv()
API_KEY = os.getenv("ODDS_API_KEY")

#The ODDS API endpoint for NBA
sport = "basketball_nba"
url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/"

#parameters for the API request
params = {
    "apiKey": API_KEY, #key
    "regions": "us", #US sportsbooks
    "markets": "spread", #player points market
}

#call the API
response = requests.get(url, params=params)
print(response.status_code)
print(response.text)
# data = response.json()

# print(data)
# for item in data[:3]:
#     print(item)

