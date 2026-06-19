# tricolor-janken

A modern desktop application for **Tricolor Rock-Paper-Scissors (三色じゃんけん)**, an incomplete information card game.
Features a mathematically unbeatable AI trained via CFR (Counterfactual Regret Minimization).

## Project structure

```
tricolor-janken/
├── core/           # Python simulator & CFR learning logic
│   ├── game.py     # Card encoding, GameState, information set
│   ├── cfr.py      # Vanilla CFR + External Sampling MCCFR
│   └── train.py    # Training entry point
├── frontend/       # UI (Tauri / Flutter / PySide6 — Phase 2)
├── docs/           # Progress log
└── README.md
```

## AI Training (Phase 1)

Requires Python 3.9+.  No external dependencies beyond the standard library.

```bash
# Default: External Sampling MCCFR, 100 000 iterations
python -m core.train

# Continue training from a saved checkpoint
python -m core.train --load weights.pkl --iter 500000

# Vanilla CFR (exhaustive tree traversal — for testing only)
python -m core.train --method vanilla --iter 500
```

Trained weights are saved as `weights.pkl` (excluded from version control).
