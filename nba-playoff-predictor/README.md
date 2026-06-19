# 🏀 NBA Playoff Predictor

A full-stack Python MVP that predicts NBA regular-season game winners, simulates
playoff series and brackets from predicted probabilities, and visualises player
and team statistics — all in an interactive Streamlit dashboard.

> ⚠️ Educational baseline only. **Not betting advice.**

---

## Features

- **Regular-season game prediction** — logistic-regression model trained on
  leakage-free pre-game features.
- **Playoff simulation** — Monte-Carlo best-of-seven series (2-2-1-1-1 home
  court) and full 16-team bracket simulation.
- **Player stat visualisation** — per-game charts with rolling 5-game averages,
  plus season-by-season and career tables (toggle per-game / totals).
- **Team stat visualisation** — scoring, plus-minus, and rolling last-10 trends.
- **Schedule / current season** — pick any date (defaults to today): upcoming
  games show each team's predicted win %, finished games show the final score
  and an expandable box score.
- **Local caching** — NBA API responses are cached to parquet so endpoints are
  not hit repeatedly, and the app stays usable from cache when the API is down.

## Tech stack

Python 3.10+ · Streamlit · pandas · numpy · scikit-learn · Plotly · DuckDB ·
joblib · nba_api · pyarrow · pytest

## Project layout

```
nba-playoff-predictor/
├── app/                  # Streamlit UI (Home + 4 pages)
├── data/                 # raw/ + processed/ caches, nba.duckdb
├── models/               # saved model + metrics
├── src/
│   ├── config.py         # paths & constants
│   ├── db/               # DuckDB helpers
│   ├── ingest/           # NBA API fetch + parquet cache
│   ├── features/         # rolling stats, Elo, dataset assembly
│   ├── models/           # train / evaluate / predict
│   └── simulation/       # series & bracket simulation
└── tests/                # pytest suite
```

---

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv .venv

# macOS / Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt
```

## Train the model

This fetches NBA data (caching it locally), builds the modelling dataset, trains
the model, and saves it:

```bash
python -m src.models.train_game_model
```

Outputs:
- `models/game_win_model.joblib`
- `models/game_win_model_metrics.json`

If the NBA API is unavailable, the command prints a clear, friendly error.

## Run the app

```bash
streamlit run app/Home.py
```

The Home page shows whether a model exists and displays its saved metrics.

## Run tests

```bash
pytest
```

---

## How the model works

- **Baseline**: `LogisticRegression` inside a scikit-learn `Pipeline`
  (`SimpleImputer(median)` → `StandardScaler` → `LogisticRegression`).
- **Elo ratings**: each team's strength is tracked game-to-game; the rating
  attached to a game is the value *before* tip-off, with home-court advantage
  applied to the win-probability estimate.
- **Rolling last-10 stats**: points, plus-minus, rebounds, assists, turnovers,
  etc., averaged over the previous 10 games.
- **Rest days & back-to-backs**: days since each team's previous game.
- **No data leakage**:
  - rolling features use `shift(1)` so a game never sees its own box score;
  - Elo ratings update only *after* a game is recorded;
  - a **time-based** 80/20 train/test split (earliest games train, latest test)
    instead of a random split.
- **Evaluation**: accuracy, log loss, and Brier score on the held-out tail.

## Known limitations

- `nba_api` endpoints can be **slow or temporarily unavailable**; the app falls
  back to cached data where possible.
- Player **injuries / availability** are not modelled yet.
- The model is a **baseline**, not tuned and **not betting advice**.
- The playoff bracket is **manually selected** in this MVP (no live standings).

## Future improvements

- Advanced box-score / tracking features.
- Injury and availability data.
- Live standings to auto-build the bracket.
- Gradient-boosted models (XGBoost / LightGBM).
- Probability calibration (e.g. isotonic / Platt scaling).
- Shot charts and richer player visualisations.
- Cloud deployment.
