# FPL Intelligence

A Python analytics project for Fantasy Premier League player ranking, captaincy, transfer decisions, and model backtesting.

## First Milestone

Fetch live FPL data, convert players into a `pandas` DataFrame, and print a basic player ranking.

## Setup

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

## Run

```powershell
python -m fpl_intelligence.fetch_fpl
```

## Roadmap

- Fetch and store FPL API data
- Build player feature tables
- Create expected-points baselines
- Add captaincy rankings
- Add transfer recommendations
- Backtest model decisions against historical gameweeks
- Build a Streamlit dashboard
