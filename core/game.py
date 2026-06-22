"""
Game engine for Tricolor Rock-Paper-Scissors (三色じゃんけん).

Card encoding: card = shape * 3 + color  (0..8)
  shape : 0=GU(グー)  1=CHOKI(チョキ)  2=PA(パー)
  color : 0=WHITE(白,1pt)  1=BLUE(青,2pt)  2=RED(赤,3pt)

Hand representation: 9-bit bitmask (bit i set ⟺ card i in hand).
"""
from __future__ import annotations
from typing import List, Tuple

POINTS = (1, 2, 3)          # indexed by color
FULL_HAND = (1 << 9) - 1   # all 9 cards

# Janken outcome table: _J[s1][s2] from s1's perspective
#  +1 = s1 wins,  -1 = s2 wins,  0 = draw
_J: Tuple[Tuple[int, ...], ...] = (
    ( 0,  1, -1),  # GU    beats CHOKI, loses to PA
    (-1,  0,  1),  # CHOKI beats PA,    loses to GU
    ( 1, -1,  0),  # PA    beats GU,    loses to CHOKI
)


def janken(s1: int, s2: int) -> int:
    return _J[s1][s2]


def card_shape(card: int) -> int:
    return card // 3


def card_color(card: int) -> int:
    return card % 3


def hand_to_list(hand: int) -> List[int]:
    return [i for i in range(9) if hand >> i & 1]


# ── Human-readable labels ──────────────────────────────────────────────────────

SHAPE_NAMES = ('グー', 'チョキ', 'パー')
COLOR_NAMES = ('白', '青', '赤')

def card_name(card: int) -> str:
    return f'{SHAPE_NAMES[card_shape(card)]}{COLOR_NAMES[card_color(card)]}'


# ── GameState ──────────────────────────────────────────────────────────────────

class GameState:
    """
    Minimal complete game state for CFR traversal.

    Phase model (per round)
    -----------------------
    phase 0 — first player (先手) selects a card and places it face-down.
               Only the card's COLOR is revealed to the second player.
    phase 1 — second player (後手) selects a card.  Both cards are then
               flipped; janken result is computed and scores updated.

    After 9 rounds (round_num == 9) the state is terminal.

    Fields
    ------
    hands     : [hand0, hand1]  — 9-bit bitmask per player
    scores    : [score0, score1]
    first     : index (0 or 1) of the first player in the current round
    round_num : number of completed rounds (0..9)
    phase     : 0 or 1 (see above)
    pending   : card played by first player while in phase 1 (-1 otherwise)
    history   : list of (fp_card, sp_card, result) for completed rounds
                result: +1 = first player won, -1 = second player won, 0 = draw
    """

    __slots__ = ('hands', 'scores', 'first', 'round_num', 'phase', 'pending', 'history')

    def __init__(self, first: int = 0) -> None:
        self.hands: List[int] = [FULL_HAND, FULL_HAND]
        self.scores: List[int] = [0, 0]
        self.first: int = first
        self.round_num: int = 0
        self.phase: int = 0
        self.pending: int = -1
        self.history: List[Tuple[int, int, int]] = []

    def copy(self) -> GameState:
        s = object.__new__(GameState)
        s.hands     = self.hands.copy()
        s.scores    = self.scores.copy()
        s.first     = self.first
        s.round_num = self.round_num
        s.phase     = self.phase
        s.pending   = self.pending
        s.history   = self.history.copy()
        return s

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def is_terminal(self) -> bool:
        return self.round_num == 9

    @property
    def current_player(self) -> int:
        """Index of the player who must act next."""
        return self.first if self.phase == 0 else 1 - self.first

    def legal_actions(self) -> List[int]:
        """Cards the current player may play (list of card indices 0..8)."""
        return hand_to_list(self.hands[self.current_player])

    # ── State transition ──────────────────────────────────────────────────

    def step(self, card: int) -> GameState:
        """
        Return a new GameState after the current player plays `card`.
        Does NOT validate that `card` is in the player's hand.
        """
        s = self.copy()
        p = self.current_player
        s.hands[p] ^= 1 << card   # remove card from hand

        if s.phase == 0:
            # First player places card face-down; move to phase 1.
            s.pending = card
            s.phase   = 1
            return s

        # Phase 1: second player has played → resolve the round.
        fp, sp   = s.first, 1 - s.first
        fp_card  = s.pending          # first player's card
        sp_card  = card               # second player's card
        result   = janken(card_shape(fp_card), card_shape(sp_card))

        if result == 1:               # first player wins
            s.scores[fp] += POINTS[card_color(fp_card)]
            s.first = fp
        elif result == -1:            # second player wins
            s.scores[sp] += POINTS[card_color(sp_card)]
            s.first = sp
        else:                         # draw → second player becomes first
            s.first = sp

        s.history.append((fp_card, sp_card, result, fp))
        s.round_num += 1
        s.phase   = 0
        s.pending = -1
        return s

    # ── Utility ───────────────────────────────────────────────────────────

    def utility(self, player: int) -> float:
        """Win/loss/draw utility for `player` at a terminal state."""
        assert self.is_terminal, 'utility() called on non-terminal state'
        d = self.scores[player] - self.scores[1 - player]
        return 1.0 if d > 0 else (-1.0 if d < 0 else 0.0)

    # ── Information set ───────────────────────────────────────────────────

    def info_set_key(self) -> str:
        """
        Compact string key for the current player's information set.

        A player observes:
          - their own remaining hand (bitmask)
          - all completed rounds (both cards revealed after each round)
          - current scores and who is first this round
          - (phase 1 only) the COLOR of the first player's pending card,
            but NOT its shape — the central imperfect-information element

        History is encoded as a fixed-width string: one char per value,
        three chars per round: '{fp_card}{sp_card}{result+1}'.
        """
        p    = self.current_player
        hist = ''.join(f'{a}{b}{r + 1}' for a, b, r, *_ in self.history)
        key  = f'{p}|{self.hands[p]}|{self.scores[0]}-{self.scores[1]}|{self.first}|{hist}'
        if self.phase == 1:
            # Second player sees colour of pending card (values 0/1/2)
            key += f'|c{card_color(self.pending)}'
        return key

    # ── Debug helpers ─────────────────────────────────────────────────────

    def __repr__(self) -> str:
        hand_str = [
            '[' + ' '.join(card_name(c) for c in hand_to_list(self.hands[i])) + ']'
            for i in range(2)
        ]
        return (
            f'GameState(round={self.round_num}/9, phase={self.phase}, '
            f'first={self.first}, scores={self.scores}, '
            f'P0={hand_str[0]}, P1={hand_str[1]})'
        )
