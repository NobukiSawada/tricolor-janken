import { useState, useEffect, useCallback } from 'react';
import './App.css';
import { api } from './api';
import type { GameView, RoundRecord } from './types';
import { Card, FaceDownCard } from './components/Card';
import { HistoryPanel } from './components/HistoryPanel';

type Screen = 'start' | 'playing' | 'round_result' | 'game_over';

const VERDICT: Record<string, string> = {
  human_win: 'あなたの勝ち！',
  ai_win:    'AIの勝ち',
  draw:      'あいこ',
};

export default function App() {
  const [screen, setScreen]         = useState<Screen>('start');
  const [game, setGame]             = useState<GameView | null>(null);
  const [lastRound, setLastRound]   = useState<RoundRecord | null>(null);
  const [pendingGame, setPendingGame] = useState<GameView | null>(null);
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState<string | null>(null);

  const handleNewGame = async () => {
    setLoading(true);
    setError(null);
    try {
      const g = await api.newGame();
      setGame(g);
      setLastRound(null);
      setPendingGame(null);
      setScreen('playing');
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleCardPlay = useCallback(async (cardId: number) => {
    if (!game || loading) return;
    setLoading(true);
    setError(null);
    try {
      const next = await api.play(cardId);
      if (next.history.length > game.history.length) {
        // A round just completed — show result briefly
        const completed = next.history[next.history.length - 1];
        setLastRound(completed);
        setPendingGame(next);
        setScreen('round_result');
      } else {
        setGame(next);
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [game, loading]);

  // Auto-advance after round_result
  useEffect(() => {
    if (screen !== 'round_result' || !pendingGame) return;
    const id = setTimeout(() => {
      setGame(pendingGame);
      setPendingGame(null);
      setScreen(pendingGame.is_terminal ? 'game_over' : 'playing');
    }, 2200);
    return () => clearTimeout(id);
  }, [screen, pendingGame]);

  // ── Start screen ─────────────────────────────────────────────────────────────

  if (screen === 'start') {
    return (
      <div className="app">
        <div className="start-screen">
          <h1 className="start-screen__title">三色じゃんけん</h1>
          <p className="start-screen__subtitle">
            グー・チョキ・パー × 白・青・赤　全9ラウンド制
          </p>
          {error && <div className="error-banner">{error}</div>}
          <button className="btn-primary" onClick={handleNewGame} disabled={loading}>
            {loading ? '準備中...' : 'ゲームスタート'}
          </button>
        </div>
      </div>
    );
  }

  // ── Game over screen ──────────────────────────────────────────────────────────

  if (screen === 'game_over' && game) {
    const winnerLabel = game.winner === 'human' ? '🎉 あなたの勝利！'
                      : game.winner === 'ai'    ? '😞 AIの勝利'
                      : '🤝 引き分け';
    const cls = `game-over__result game-over__result--${game.winner ?? 'draw'}`;
    return (
      <div className="app">
        <div className="game-over">
          <div className={cls}>{winnerLabel}</div>
          <div className="game-over__score">
            あなた {game.human_score}点 <span>vs</span> AI {game.ai_score}点
          </div>
          <HistoryPanel history={game.history} />
          <button className="btn-primary" onClick={handleNewGame} disabled={loading}>
            もう一度プレイ
          </button>
        </div>
      </div>
    );
  }

  // ── Playing / round_result ────────────────────────────────────────────────────

  if (!game) return null;
  const isMyTurn = game.is_human_turn && screen === 'playing' && !loading;

  return (
    <div className="app">
      {/* Round result overlay */}
      {screen === 'round_result' && lastRound && (
        <div className="round-result">
          <div className="round-result__box">
            <div className="round-result__title">ラウンド {lastRound.round_num} 結果</div>
            <div className="round-result__cards">
              <div className="battle-slot">
                <div className="battle-slot__label">あなた {lastRound.human_was_first ? '（先手）' : '（後手）'}</div>
                <Card card={lastRound.human_card} />
              </div>
              <div className="battle-zone__vs">vs</div>
              <div className="battle-slot">
                <div className="battle-slot__label">AI {lastRound.human_was_first ? '（後手）' : '（先手）'}</div>
                <Card card={lastRound.ai_card} />
              </div>
            </div>
            <div className={`round-result__verdict round-result__verdict--${lastRound.result}`}>
              {VERDICT[lastRound.result]}
            </div>
            {(lastRound.human_points > 0 || lastRound.ai_points > 0) && (
              <div className="round-result__pts">
                {lastRound.human_points > 0
                  ? `あなた +${lastRound.human_points}点`
                  : `AI +${lastRound.ai_points}点`}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Score header */}
      <header className="score-header">
        <div>
          <div className="score-header__title">三色じゃんけん</div>
          <div className="score-header__round">Round {game.round + 1} / 9</div>
        </div>
        <div className="score-header__scores">
          <div className="score-item score-item--human">
            <span className="score-item__label">あなた</span>
            <span className="score-item__value">{game.human_score}</span>
          </div>
          <span className="score-header__sep">:</span>
          <div className="score-item score-item--ai">
            <span className="score-item__label">AI</span>
            <span className="score-item__value">{game.ai_score}</span>
          </div>
        </div>
      </header>

      <div className="game-screen">
        {error && <div className="error-banner">{error}</div>}

        {/* AI zone */}
        <div className="zone-label">AIの手札</div>
        <div className="ai-zone">
          <div className="ai-hand">
            {Array.from({ length: game.ai_card_count }).map((_, i) => (
              <FaceDownCard key={i} />
            ))}
          </div>
        </div>

        {/* Battle zone */}
        <div className="battle-zone">
          {game.pending_color_name ? (
            <>
              <div className="battle-slot">
                <div className="battle-slot__label">AIが出した（色のみ公開）</div>
                <FaceDownCard colorHint={game.pending_color_name} />
              </div>
              <div className="battle-zone__vs">vs</div>
              <div className="battle-slot">
                <div className="battle-slot__label">あなたのカード</div>
                <div className="card card--facedown" style={{ opacity: 0.3 }}>
                  <span className="card__back-mark">？</span>
                </div>
              </div>
            </>
          ) : (
            <div className="battle-zone__status">
              {game.is_human_first ? (
                <>
                  <strong>あなたが先手です</strong>
                  <br />
                  カードを1枚選んでください。<br />
                  <small>あなたのカードの「色」のみAIに公開されます</small>
                </>
              ) : (
                <>
                  <strong>AIが先手です</strong>
                  <br />
                  AIがカードを選んでいます…
                </>
              )}
            </div>
          )}
        </div>

        {/* Human zone */}
        <div className="human-zone">
          <div className="zone-label">あなたの手札</div>
          <div className="human-hand">
            {game.human_hand.map(card => (
              <Card
                key={card.id}
                card={card}
                onClick={isMyTurn ? () => handleCardPlay(card.id) : undefined}
                disabled={!isMyTurn}
              />
            ))}
          </div>
          <div className={`human-zone__instruction ${isMyTurn ? 'human-zone__instruction--active' : ''}`}>
            {isMyTurn
              ? 'カードをクリックして出してください'
              : loading
              ? 'AIが考えています...'
              : ''}
          </div>
        </div>

        <HistoryPanel history={game.history} />

        <button className="btn-secondary" onClick={handleNewGame} disabled={loading}>
          最初からやり直す
        </button>
      </div>
    </div>
  );
}
