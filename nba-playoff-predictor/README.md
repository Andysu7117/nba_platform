# 🏀 Hardwood — NBA Platform

A full-stack NBA analytics platform:

- **Backend** — a modular **FastAPI** service that wraps the data-science domain
  code (`src/`) behind clean, typed JSON routes.
- **Frontend** — a **React + TypeScript + Vite** single-page app (the "Hardwood"
  design) that talks to the API over `/api`.

It predicts regular-season game winners, simulates the playoff bracket, and
visualises standings, schedules and league-wide player stats — all from
**pre-game features only** (Elo, rolling last-10 form, rest) with a time-based
train/test split to avoid leakage. The baseline model is a logistic regression.

> ⚠️ Educational baseline only. **Not betting advice.**

---

## Architecture

```
nba-playoff-predictor/
├── api/                # FastAPI web layer (thin, framework-only)
│   ├── main.py         #   app + router wiring  →  /api/*
│   ├── reference/      #   static team metadata (conference, colour, city)
│   ├── schemas/        #   Pydantic request/response models
│   ├── services/       #   business logic bridging api ↔ src
│   └── routers/        #   one module per resource group
├── src/                # Domain logic (no web framework) — ingest, features,
│                       #   model, simulation. Reusable from scripts & tests.
├── scripts/            # Maintenance scripts (cache warming)
├── frontend/           # React + TypeScript + Vite app
│   └── src/
│       ├── api/        #   typed client + types mirroring the schemas
│       ├── components/ #   shared UI (Sidebar, TeamChip, box-score modal, …)
│       ├── pages/      #   one component per screen
│       ├── hooks/      #   useAsync data-fetching hook
│       └── context/    #   theme (light/dark) provider
└── tests/              # pytest (domain + API smoke tests)
```

The web layer never touches pandas/sklearn directly — routers call
`api.services`, which call `src`. That keeps `src` independently testable and the
routers thin.

---

## Quick start

### 1. Backend (FastAPI)

```bash
cd nba-playoff-predictor
python -m venv .venv
source .venv/Scripts/activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# Train the model + fetch/cache NBA data (first run only; needs internet):
python -m src.models.train_game_model
# Optional: warm the player-leaderboard cache:
python -m scripts.fetch_player_leaderboard

# Run the API (interactive docs at http://localhost:8000/api/docs):
uvicorn api.main:app --reload
```

### 2. Frontend (React)

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173  (proxies /api → :8000)
```

Open <http://localhost:5173>.

---

## API overview

All routes are mounted under `/api`; interactive docs live at `/api/docs`.

| Method | Path                              | Purpose                                  |
| ------ | --------------------------------- | ---------------------------------------- |
| GET    | `/meta`                           | Current season, latest date, model flags |
| GET    | `/meta/model`                     | Trained-model metrics                    |
| GET    | `/teams`                          | All 30 teams + current records           |
| GET    | `/standings?conference=East`      | Conference / league standings            |
| GET    | `/schedule?date=YYYY-MM-DD`       | Games for a date (+ model win prob)      |
| GET    | `/schedule/calendar?start=&end=`  | Per-day game counts (week strip)         |
| GET    | `/games/{game_id}/boxscore`       | Player box score for a finished game     |
| POST   | `/predict`                        | Win prob, projected score, key factors   |
| GET    | `/playoffs/seeds`                 | Default top-8 seeds per conference        |
| POST   | `/playoffs/simulate`              | Monte-Carlo bracket + championship odds  |
| GET    | `/players`                        | League per-game leaderboard + leaders    |

Standings, schedule, predictions and playoff simulation run **fully offline**
from the cached parquet data. Box scores and the player leaderboard fetch live
from the NBA API and degrade gracefully when it is unreachable.

---

## How the model works

- **Baseline**: `LogisticRegression` inside a scikit-learn `Pipeline`
  (`SimpleImputer(median)` → `StandardScaler` → `LogisticRegression`).
- **Elo ratings**: each game uses the rating *before* tip-off, with home-court
  advantage applied only to the win-probability estimate.
- **Rolling last-10 stats** and **rest / back-to-back** flags, all `shift(1)`-ed
  so a game never sees its own box score.
- **No leakage**: Elo updates only after a game is recorded, and a **time-based**
  80/20 split (earliest games train, latest test) replaces a random split.
- **Evaluation**: accuracy, log loss, Brier score on the held-out tail.

The frontend's projected scores and "key factors" are derived from each team's
season rating profile (points for/against per game, net rating, win %).

---

## Tests

```bash
pytest                                   # domain + API smoke tests
cd frontend && npm run typecheck && npm run build
```

## Known limitations

- `nba_api` endpoints can be slow or temporarily unavailable; the platform falls
  back to cached data where possible.
- Player injuries / availability are not modelled.
- The model is an untuned baseline — **not betting advice**.
- Off/def "ratings" are points scored/allowed per game (not per-100-possessions).
