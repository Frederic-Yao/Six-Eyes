# Six-Eyes: NBA Player Prop Analytics

A Python-based analytics pipeline that ingests NBA player and team game logs, caches data locally to avoid API throttling, and evaluates player prop bets using historical performance, matchup context, and scheduling effects.

## Features
- Automated ingestion of NBA player and team game logs
- Disk caching to avoid repeated API calls and rate limits
- Advanced prop projections using rolling averages
- Adjusts projections depending on matchup factors (e.g., head-to-head, game pace, defensive ratings)
- Detects back-to-back games for players and opponents
- Modular project structure for easy extension

## Tech Stack
- Python
- pandas, NumPy, SciPy
- nba_api, requests
- CSV-based data caching

## Example Workflow
1. Fetch daily NBA player props
2. Load or cache historical game logs
3. Evaluate model probability vs implied odds
4. Identify positive expected value props

## Limitations
- Currently, NBA stats API blocks high-volume requests, so fully automated evaluation of all props is limited.  
- Pipeline and caching are fully implemented; once API access is unrestricted, automation will work as intended.

## Highlights / Skills Demonstrated
- Handling unreliable APIs and avoiding rate limits with caching
- Building an analytics pipeline from raw NBA data
- Applying statistical models and domain-specific logic to sports betting data
- Writing modular, maintainable Python code

## Future Improvements
- Add automated notifications for best prop edges
- Expand model to account for player injuries and lineup changes
- Improve caching mechanism for faster performance
- Explore alternative data sources to avoid API rate limits

## Disclaimer
This project is for educational and analytical purposes only.
