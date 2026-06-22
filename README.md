# tricolor-janken

A modern desktop application for **Tricolor Rock-Paper-Scissors (三色じゃんけん)**, an incomplete information card game.
Features a mathematically unbeatable AI trained via CFR (Counterfactual Regret Minimization).

## Project structure

```
tricolor-janken/
├── core/           # Python simulator & CFR learning logic
│   ├── game.py     # Card encoding, GameState, information set
│   ├── cfr.py      # Vanilla CFR + Outcome Sampling MCCFR
│   └── train.py    # Training entry point
├── api/            # FastAPI bridge (Python ↔ React frontend)
│   └── main.py
├── frontend/       # React + TypeScript UI (Vite / Tauri)
└── README.md
```

## How to run (development)

Requires Python 3.9+ and Node.js 18+.

```bash
# Terminal 1 — Python API server
pip install fastapi uvicorn
python api/main.py

# Terminal 2 — React dev server
cd frontend
npm install
npm run dev
# → Open http://localhost:5173
```

## AI Training

```bash
# Outcome Sampling MCCFR, 500 000 iterations (recommended)
python -m core.train --iter 500000

# Continue training from a checkpoint
python -m core.train --load weights.pkl --iter 500000

# Vanilla CFR (exhaustive — for testing only)
python -m core.train --method vanilla --iter 500
```

Trained weights are saved as `weights.pkl` (excluded from version control).
Once trained, restart `python api/main.py` to enable the CFR strategy.
