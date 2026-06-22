"""
CFR solver for Tricolor Janken.

Two variants are provided:

Vanilla CFR
    Exhaustive tree traversal every iteration.
    Guaranteed convergence; practical only for small subtrees or testing.

Outcome Sampling MCCFR  (default / recommended)
    Samples exactly ONE action at every node (both players).
    O(game_depth) work per iteration instead of O(actions^depth).
    Scales to hundreds of thousands of iterations per minute.
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
        self.regret_sum: StrategyMap = defaultdict(lambda: defaultdict(float))
        self.strategy_sum: StrategyMap = defaultdict(lambda: defaultdict(float))
        self.iterations: int = 0

    def _regret_match(self, info_set: str, actions: List[int]) -> Dict[int, float]:
        """Regret-matching: compute current mixed strategy from cumulative regrets."""
        regrets = self.regret_sum[info_set]
        pos = {a: max(0.0, regrets[a]) for a in actions}
        total = sum(pos.values())
        if total > 0.0:
            return {a: pos[a] / total for a in actions}
        n = len(actions)
        return {a: 1.0 / n for a in actions}

    # -------------------------------------------------------------------------
    # Vanilla CFR
    # -------------------------------------------------------------------------

    def _vanilla_cfr(self, state: GameState, p0: float, p1: float) -> float:
        """Recursive vanilla CFR. Returns expected utility for player 0."""
        if state.is_terminal:
            return state.utility(0)

        player   = state.current_player
        actions  = state.legal_actions()
        info_set = state.info_set_key()
        sigma    = self._regret_match(info_set, actions)

        pi = p0 if player == 0 else p1
        for a in actions:
            self.strategy_sum[info_set][a] += pi * sigma[a]

        action_utils: Dict[int, float] = {}
        node_util = 0.0
        for a in actions:
            cp0 = p0 * sigma[a] if player == 0 else p0
            cp1 = p1 * sigma[a] if player == 1 else p1
            u   = self._vanilla_cfr(state.step(a), cp0, cp1)
            action_utils[a] = u
            node_util      += sigma[a] * u

        pi_neg = p1 if player == 0 else p0
        sign   = 1.0 if player == 0 else -1.0
        for a in actions:
            self.regret_sum[info_set][a] += sign * pi_neg * (action_utils[a] - node_util)

        return node_util

    def train_vanilla(self, iterations: int, verbose: bool = True) -> None:
        """Run vanilla CFR (exhaustive). Use only for small-scale testing."""
        for i in range(iterations):
            for first in (0, 1):
                self._vanilla_cfr(GameState(first=first), 0.5, 0.5)
            self.iterations += 1
            if verbose and (i + 1) % 100 == 0:
                print(f'[Vanilla CFR] {i + 1}/{iterations}  '
                      f'info_sets={len(self.strategy_sum)}')

    # -------------------------------------------------------------------------
    # Outcome Sampling MCCFR
    # -------------------------------------------------------------------------

    def _outcome_cfr(self, state: GameState, updating_player: int,
                     pi_i: float, pi_neg: float) -> float:
        """
        Outcome Sampling MCCFR.

        Samples exactly ONE action at every node — O(game_depth) per call.

        pi_i  : reach probability of updating_player under current strategy sigma
        pi_neg: reach probability of the opponent under sigma

        Returns: estimated utility for updating_player at the sampled terminal.
        """
        if state.is_terminal:
            return state.utility(updating_player)

        player   = state.current_player
        actions  = state.legal_actions()
        info_set = state.info_set_key()
        sigma    = self._regret_match(info_set, actions)
        n        = len(actions)

        if player == updating_player:
            # Epsilon-greedy: guarantees every action is explored
            eps = 0.6
            q   = {a: eps / n + (1.0 - eps) * sigma[a] for a in actions}
            a   = random.choices(actions, weights=[q[x] for x in actions], k=1)[0]

            util = self._outcome_cfr(
                state.step(a), updating_player,
                pi_i * sigma[a], pi_neg,
            )

            # Regret update (sum over all actions == 0, zero-sum property)
            for x in actions:
                if x == a:
                    self.regret_sum[info_set][x] += pi_neg * (1.0 - sigma[x]) * util
                else:
                    self.regret_sum[info_set][x] -= pi_neg * sigma[x] * util

            for x in actions:
                self.strategy_sum[info_set][x] += pi_i * sigma[x]

            return util
        else:
            a = random.choices(actions, weights=[sigma[x] for x in actions], k=1)[0]
            return self._outcome_cfr(
                state.step(a), updating_player,
                pi_i, pi_neg * sigma[a],
            )

    def train_mccfr(self, iterations: int, verbose: bool = True) -> None:
        """
        Run Outcome Sampling MCCFR for `iterations` iterations.

        Each iteration samples 4 trajectories
        (2 first-player orderings x 2 updating players).
        Typical throughput: hundreds of thousands of iterations per minute.
        """
        for i in range(iterations):
            for first in (0, 1):
                state = GameState(first=first)
                self._outcome_cfr(state, 0, 0.5, 0.5)
                self._outcome_cfr(state, 1, 0.5, 0.5)
            self.iterations += 1
            if verbose and (i + 1) % 100_000 == 0:
                print(f'[MCCFR] {i + 1}/{iterations}  '
                      f'info_sets={len(self.strategy_sum)}')

    # -------------------------------------------------------------------------
    # Strategy retrieval
    # -------------------------------------------------------------------------

    def average_strategy(self) -> StrategyMap:
        """Return the average strategy (Nash equilibrium approximation)."""
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
        """Return average strategy probabilities for a specific info set."""
        sums = self.strategy_sum.get(info_set_key)
        if sums is None:
            n = len(actions)
            return {a: 1.0 / n for a in actions}
        total = sum(sums.get(a, 0.0) for a in actions)
        if total > 0.0:
            return {a: sums.get(a, 0.0) / total for a in actions}
        n = len(actions)
        return {a: 1.0 / n for a in actions}

    # -------------------------------------------------------------------------
    # Persistence
    # -------------------------------------------------------------------------

    def save(self, path: str) -> None:
        with open(path, 'wb') as f:
            pickle.dump({
                'regret_sum':   dict(self.regret_sum),
                'strategy_sum': dict(self.strategy_sum),
                'iterations':   self.iterations,
            }, f)
        print(f'Saved -> {path}  ({self.iterations} iterations, '
              f'{len(self.strategy_sum)} info sets)')

    @classmethod
    def load(cls, path: str) -> CFRSolver:
        solver = cls()
        with open(path, 'rb') as f:
            data = pickle.load(f)
        solver.regret_sum.update(data['regret_sum'])
        solver.strategy_sum.update(data['strategy_sum'])
        solver.iterations = data['iterations']
        print(f'Loaded <- {path}  ({solver.iterations} iterations, '
              f'{len(solver.strategy_sum)} info sets)')
        return solver
