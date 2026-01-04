# NBA Player Prop Evaluation Engine

A Python-based analytics pipeline that ingests NBA player and team game logs,
caches data locally to avoid API throttling, and evaluates player prop bets
using historical performance, matchup context, and scheduling effects.

## Features
- Automated ingestion of NBA player and team game logs
- Disk caching to avoid repeated API calls and rate limits
- Advanced prop projection using rolling averages
- Adjusts projection depending on factor filters (e.g. head to head matchups, game pace, defensive ratings etc.)
- Back-to-back game detection for players and opponents
- Modular project structure for easy extension

## Tech Stack
- Python
- pandas
- nba_api
- requests
- CSV-based data caching

## Example Workflow
1. Fetch daily NBA player props
2. Load or cache historical game logs
3. Evaluate model probability vs implied odds
4. Identify positive expected value props

## Disclaimer
This project is for educational and analytical purposes only.
