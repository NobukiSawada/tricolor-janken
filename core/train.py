"""
Training entry point for the Tricolor Janken CFR AI.

Usage examples
--------------
# MCCFR, 100 000 iterations (default)
python -m core.train

# Vanilla CFR, 500 iterations (exhaustive — slow for full game)
python -m core.train --method vanilla --iter 500

# Resume training from saved weights
python -m core.train --load weights.pkl --iter 200000

# Save to a specific path without progress output
python -m core.train --save models/cfr_v1.pkl --quiet
"""
from __future__ import annotations

import argparse
import os
import sys

from .cfr import CFRSolver


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Train CFR AI for Tricolor Janken (三色じゃんけん)'
    )
    parser.add_argument(
        '--method', choices=['vanilla', 'mccfr'], default='mccfr',
        help='CFR variant: "mccfr" (fast, recommended) or "vanilla" (exhaustive)',
    )
    parser.add_argument(
        '--iter', type=int, default=100_000,
        help='Number of training iterations (default: 100 000)',
    )
    parser.add_argument(
        '--load', type=str, default=None,
        help='Path to an existing weights file to continue training from',
    )
    parser.add_argument(
        '--save', type=str, default='weights.pkl',
        help='Output path for trained weights (default: weights.pkl)',
    )
    parser.add_argument(
        '--quiet', action='store_true',
        help='Suppress per-iteration progress output',
    )
    args = parser.parse_args()

    # ── Load or create solver ──────────────────────────────────────────────
    if args.load and os.path.exists(args.load):
        solver = CFRSolver.load(args.load)
    else:
        if args.load:
            print(f'Warning: {args.load!r} not found — starting fresh.', file=sys.stderr)
        solver = CFRSolver()

    # ── Train ──────────────────────────────────────────────────────────────
    print(f'Method : {args.method.upper()}')
    print(f'Iters  : {args.iter:,}')
    print(f'Save → : {args.save}')
    print()

    verbose = not args.quiet
    if args.method == 'vanilla':
        solver.train_vanilla(args.iter, verbose=verbose)
    else:
        solver.train_mccfr(args.iter, verbose=verbose)

    # ── Save ───────────────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(os.path.abspath(args.save)) or '.', exist_ok=True)
    solver.save(args.save)
    print(f'\nDone.  Total iterations : {solver.iterations:,}')
    print(f'       Info sets found  : {len(solver.strategy_sum):,}')


if __name__ == '__main__':
    main()
