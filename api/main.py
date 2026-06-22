"""
FastAPI bridge between React frontend and Python CFR game engine.

Run:
    python -m uvicorn api.main:app --reload
or:
    python -m api.main
"""
from __future__ import annotations

import os
import random
import sys
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.game import (
    GameState, card_color, card_shape, hand_to_list,
    COLOR_NAMES, SHAPE_NAMES, POINTS,
)
from core.cfr import CFRSolver

app = FastAPI(title='Tricolor Janken API')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)

# ── Load trained weights if available ─────────────────────────────────────────

_solver: Optional[CFRSolver] = None
_weights_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'weights.pkl',
)
if os.path.exists(_weights_path):
    try:
        _solver = CFRSolver.load(_weights_path)
        print(f'AI: loaded trained weights ({_solver.iterations:,} iterations)')
    except Exception as e:
        print(f'AI: failed to load weights ({e}), using random play')
else:
    print('AI: weights.pkl not found, using random play')

# ── Session state ──────────────────────────────────────────────────────────────

_session: Optional[dict] = None   # {state, human, round_firsts}
HUMAN = 0   # human is always player 0 from the AI's perspective internally
AI    = 1


# ── Helpers ────────────────────────────────────────────────────────────────────

def _card_dict(card: int) -> dict:
    return {
        'id':     card,
        'shape':  SHAPE_NAMES[card_shape(card)],
        'color':  COLOR_NAMES[card_color(card)],
        'points': POINTS[card_color(card)],
    }


def _ai_action(state: GameState) -> int:
    actions = state.legal_actions()
    if _solver is not None:
        key   = state.info_set_key()
        probs = _solver.action_probs(key, actions)
        return random.choices(list(probs.keys()), weights=list(probs.values()), k=1)[0]
    return random.choice(actions)


def _advance_ai(session: dict) -> None:
    """Auto-play the AI's turns until it's the human's turn or game over."""
    state = session['state']
    while not state.is_terminal and state.current_player == AI:
        round_first = state.first   # first player of the current round (valid in both phases)
        old_round   = state.round_num
        action      = _ai_action(state)
        state       = state.step(action)
        if state.round_num > old_round:
            session['round_firsts'].append(round_first)
    session['state'] = state


def _build_view(session: dict) -> dict:
    state  = session['state']
    firsts = session['round_firsts']

    # ── History ────────────────────────────────────────────────────────────────
    history: List[dict] = []
    for i, (fp_card, sp_card, result, first_idx) in enumerate(state.history):
        human_was_first = (first_idx == HUMAN)
        if human_was_first:
            human_card, ai_card = fp_card, sp_card
        else:
            human_card, ai_card = sp_card, fp_card

        if result == 1:
            round_result = 'human_win' if human_was_first else 'ai_win'
            pts_human    = POINTS[card_color(human_card)] if human_was_first else 0
            pts_ai       = 0 if human_was_first else POINTS[card_color(ai_card)]
        elif result == -1:
            round_result = 'ai_win' if human_was_first else 'human_win'
            pts_human    = 0 if human_was_first else POINTS[card_color(human_card)]
            pts_ai       = POINTS[card_color(ai_card)] if human_was_first else 0
        else:
            round_result = 'draw'
            pts_human = pts_ai = 0

        history.append({
            'round_num':       i + 1,
            'human_card':      _card_dict(human_card),
            'ai_card':         _card_dict(ai_card),
            'human_was_first': human_was_first,
            'result':          round_result,
            'human_points':    pts_human,
            'ai_points':       pts_ai,
        })

    # ── Terminal / winner ──────────────────────────────────────────────────────
    winner = None
    if state.is_terminal:
        d = state.scores[HUMAN] - state.scores[AI]
        winner = 'human' if d > 0 else ('ai' if d < 0 else 'draw')

    # ── Pending color hint (phase 1, AI played first) ──────────────────────────
    pending_color_name = None
    if state.phase == 1 and state.first == AI:
        pending_color_name = COLOR_NAMES[card_color(state.pending)]

    return {
        'round':              state.round_num,        # completed rounds
        'phase':              state.phase,
        'human_score':        state.scores[HUMAN],
        'ai_score':           state.scores[AI],
        'human_hand':         [_card_dict(c) for c in hand_to_list(state.hands[HUMAN])],
        'ai_card_count':      bin(state.hands[AI]).count('1'),
        'is_human_first':     state.first == HUMAN,
        'is_human_turn':      state.current_player == HUMAN,
        'pending_color_name': pending_color_name,
        'history':            history,
        'is_terminal':        state.is_terminal,
        'winner':             winner,
        'ai_trained':         _solver is not None,
    }


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.post('/api/new-game')
def new_game() -> dict:
    global _session
    first = random.randint(0, 1)
    _session = {
        'state':        GameState(first=first),
        'round_firsts': [],
    }
    _advance_ai(_session)   # if AI goes first this round, let it play phase 0
    return _build_view(_session)


class PlayRequest(BaseModel):
    card_id: int


@app.post('/api/play')
def play(req: PlayRequest) -> dict:
    if _session is None:
        raise HTTPException(status_code=400, detail='No active game. Call /api/new-game first.')

    state = _session['state']
    if state.is_terminal:
        raise HTTPException(status_code=400, detail='Game is already over.')
    if state.current_player != HUMAN:
        raise HTTPException(status_code=400, detail='Not human turn.')
    if req.card_id not in state.legal_actions():
        raise HTTPException(status_code=400, detail=f'Card {req.card_id} is not a legal action.')

    round_first = state.first   # first player of the current round (valid in both phases)
    old_round   = state.round_num

    state = state.step(req.card_id)
    _session['state'] = state

    if state.round_num > old_round:
        _session['round_firsts'].append(round_first)

    # Auto-advance AI turns
    _advance_ai(_session)

    return _build_view(_session)


@app.get('/api/state')
def get_state() -> dict:
    if _session is None:
        raise HTTPException(status_code=400, detail='No active game.')
    return _build_view(_session)


# ── Dev runner ─────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('api.main:app', host='127.0.0.1', port=8000, reload=True)
