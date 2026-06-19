"""
CFR solver for Tricolor Janken.

Two variants are provided:

Vanilla CFR
    Exhaustive tree traversal every iteration.
    Guaranteed convergence; practical only for small subtrees or testing.

External Sampling MCCFR  (default / recommended)
    At the updating player's nodes: traverse ALL actions.
    At the opponent's nodes: sample ONE action from current strategy.
    Much faster per iteration; scales to millions of iterations.
    Converges to Nash equilibrium in expectation.
"""
from __future__ import annotations

import pickle
import random
from collections import defaultdict
from typing import Dict, List

from .game import GameState

StrategyMap = Dict[str, Dict[int, float]]


class CFRSolver:
    """
    CFR solver for Tricolor Janken (三色じゃんけん).

    After training, call `average_strategy()` or `action_probs()` to retrieve
    the Nash equilibrium approximation for use in the game.
    """

    def __init__(self) -> None:
        # Cumulative regret per (info_set, action)
        self.regret_sum: StrategyMap = defaultdict(lambda: defaultdict(float))
        # Cumulative strategy sum per (info_set, action) — for average strategy
        self.strategy_sum: StrategyMap = defaultdict(lambda: defaultdict(float))
        self.iterations: int = 0

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _regret_match(self, info_set: str, actions: List[int]) -> Dict[int, float]:
        """Regret-matching: compute current mixed strategy from cumulative regrets."""
        regrets = self.regret_sum[info_set]
        pos = {a: max(0.0, regrets[a]) for a in actions}
        total = sum(pos.values())
        if total > 0.0:
            return {a: pos[a] / total for a in actions}
        n = len(actions)
        return {a: 1.0 / n for a in actions}

    # ── Vanilla CFR ────────────────────────────────────────────────────────────

    def _vanilla_cfr(self, state: GameState, p0: float, p1: float) -> float:
        """
        Recursive vanilla CFR.  Returns expected utility for player 0.

        p0, p1 : reach probabilities for player 0 and player 1 respectively.
        """
        if state.is_terminal:
            return state.utility(0)

        player   = state.current_player
        actions  = state.legal_actions()
        info_set = state.info_set_key()
        sigma    = self._regret_match(info_set, actions)

        # Accumulate strategy sum weighted by this player's reach probability
        pi = p0 if player == 0 else p1
        for a in actions:
            self.strategy_sum[info_set][a] += pi * sigma[a]

        # Recurse: propagate reach probabilities down the tree
        action_utils: Dict[int, float] = {}
        node_util = 0.0
        for a in actions:
            cp0 = p0 * sigma[a] if player == 0 else p0
            cp1 = p1 * sigma[a] if player == 1 else p1
            u   = self._vanilla_cfr(state.step(a), cp0, cp1)
            action_utils[a] = u
            node_util       += sigma[a] * u

        # Regret update: weighted by the opponent's (counterfactual) reach
        pi_neg = p1 if player == 0 else p0
        sign   = 1.0 if player == 0 else -1.0   # player 1's utility = -u0
        for a in actions:
            self.regret_sum[info_set][a] += sign * pi_neg * (action_utils[a] - node_util)

        return node_util

    def train_vanilla(self, iterations: int, verbose: bool = True) -> None:
        """
        Run vanilla CFR for `iterations` rounds.
        Each round averages over both first-player assignments (chance node).
        """
        for i in range(iterations):
            for first in (0, 1):
                self._vanilla_cfr(GameState(first=first), 0.5, 0.5)
            self.iterations += 1
            if verbose and (i + 1) % 100 == 0:
                print(f'[Vanilla CFR] {i + 1}/{iterations}  '
                      f'info_sets={len(self.strategy_sum)}')

    # ── External Sampling MCCFR ────────────────────────────────────────────────

    def _external_cfr(self, state: GameState, updating_player: int) -> float:
        """
        External Sampling MCCFR for one `updating_player`.

        - Updating player's nodes : traverse ALL actions → regret / strategy update.
        - Opponent's nodes        : sample ONE action → single recursive call.

        Returns expected utility for `updating_player`.
        """
        if state.is_terminal:
            return state.utility(updating_player)

        player   = state.current_player
        actions  = state.legal_actions()
        info_set = state.info_set_key()
        sigma    = self._regret_match(info_set, actions)

        if player == updating_player:
            action_utils: Dict[int, float] = {}
            node_util = 0.0
            for a in actions:
                u               = self._external_cfr(state.step(a), updating_player)
                action_utils[a] = u
                node_util       += sigma[a] * u

            for a in actions:
                self.regret_sum[info_set][a]   += action_utils[a] - node_util
                self.strategy_sum[info_set][a] += sigma[a]

            return node_util
        else:
            # Sample one action from opponent's current strategy
            sampled = random.choices(actions, weights=[sigma[a] for a in actions], k=1)[0]
            return self._external_cfr(state.step(sampled), updating_player)

    def train_mccfr(self, iterations: int, verbose: bool = True) -> None:
        """
        Run External Sampling MCCFR for `iterations` iterations.
        Each iteration updates both players once over both first-player orderings.
        """
        for i in range(iterations):
            for first in (0, 1):
                state = GameState(first=first)
                self._external_cfr(state, 0)
                self._external_cfr(state, 1)
            self.iterations += 1
            if verbose and (i + 1) % 10_000 == 0:
                print(f'[MCCFR] {i + 1}/{iterations}  '
                      f'info_sets={len(self.strategy_sum)}')

    # ── Strategy retrieval ─────────────────────────────────────────────────────

    def average_strategy(self) -> StrategyMap:
        """
        Return the average (Nash equilibrium approximation) strategy.
        Use this — not the current regret-matched strategy — for play.
        """
        avg: StrategyMap = {}
        for info_set, sums in self.strategy_sum.items():
            total = sum(sums.values())
            if total > 0.0:
                avg[info_set] = {a: v / total for a, v in sums.items()}
            else:
                n = len(sums)
                avg[info_set] = {a: 1.0 / n for a in sums}
        return avg

    def action_probs(self, info_set_key: str, actions: List[int]) -> Dict[int, float]:
        """
        Return average strategy probabilities for a specific info set.
        Falls back to uniform if the info set was never visited.
        """
        sums = self.strategy_sum.get(info_set_key)
        if sums is None:
            n = len(actions)
            return {a: 1.0 / n for a in actions}
        total = sum(sums.get(a, 0.0) for a in actions)
        if total > 0.0:
            return {a: sums.get(a, 0.0) / total for a in actions}
        n = len(actions)
        return {a: 1.0 / n for a in actions}

    # ── Persistence ────────────────────────────────────────────────────────────

    def save(self, path: str) -> None:
        with open(path, 'wb') as f:
            pickle.dump({
                'regret_sum':   dict(self.regret_sum),
                'strategy_sum': dict(self.strategy_sum),
                'iterations':   self.iterations,
            }, f)
        print(f'Saved → {path}  ({self.iterations} iterations, '
              f'{len(self.strategy_sum)} info sets)')

    @classmethod
    def load(cls, path: str) -> CFRSolver:
        solver = cls()
        with open(path, 'rb') as f:
            data = pickle.load(f)
        solver.regret_sum.update(data['regret_sum'])
        solver.strategy_sum.update(data['strategy_sum'])
        solver.iterations = data['iterations']
        print(f'Loaded ← {path}  ({solver.iterations} iterations, '
              f'{len(solver.strategy_sum)} info sets)')
        return solver
