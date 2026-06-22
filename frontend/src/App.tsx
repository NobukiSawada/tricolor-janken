import { useState, useEffect, useCallback } from 'react';
import './App.css';
import { api } from './api';
import type { GameView, CardData, RoundRecord } from './types';
import { Card, FaceDownCard } from './components/Card';
import { HistoryPanel } from './components/HistoryPanel';

type Screen = 'start' | 'playing' | 'round_result' | 'game_over';

const VERDICT: Record<string, string> = {
  human_win: 'あなたの勝ち！',
  ai_win:    'AIの勝ち',
  draw:      'あいこ',
};

// card = shape * 3 + color  (color: 0=白, 1=青, 2=赤)
// Display order: 白→赤→青, within each color グー→チョキ→パー
// color priority: 白(0)→0, 青(1)→1, 赤(2)→2
const COLOR_SORT_PRIORITY: Record<number, number> = { 0: 0, 1: 1, 2: 2 };

function sortHand(hand: CardData[]): CardData[] {
  return [...hand].sort((a, b) => {
    const keyA = COLOR_SORT_PRIORITY[a.id % 3] * 3 + Math.floor(a.id / 3);
    const keyB = COLOR_SORT_PRIORITY[b.id % 3] * 3 + Math.floor(b.id / 3);
    return keyA - keyB;
  });
}

function RulesModal({ onClose }: { onClose: () => void }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal__title">三色じゃんけん — ゲームルール</div>

        <div className="modal__section">
          <div className="modal__section-title">カード</div>
          <p className="modal__text">
            各プレイヤーはグー・チョキ・パー × 白・赤・青 の計9枚のカードを持ちます。
            各カードは1回しか使えません。
          </p>
        </div>

        <hr className="modal__divider" />

        <div className="modal__section">
          <div className="modal__section-title">勝ち点（カードの色）</div>
          <div className="modal__color-row">
            <div className="modal__color-chip">
              <span className="chip chip--white" />白カード：1点
            </div>
            <div className="modal__color-chip">
              <span className="chip chip--red" />赤カード：3点
            </div>
            <div className="modal__color-chip">
              <span className="chip chip--blue" />青カード：2点
            </div>
          </div>
          <p className="modal__text" style={{ marginTop: '8px' }}>
            じゃんけんに勝ったプレイヤーが、<strong>自分が出したカードの色</strong>に応じた点数を獲得します。引き分けは得点なし。
          </p>
        </div>

        <hr className="modal__divider" />

        <div className="modal__section">
          <div className="modal__section-title">ラウンドの流れ</div>
          <p className="modal__text">
            ① 先手がカードを1枚選んで伏せる。このとき<strong>カードの「色」のみ</strong>後手に公開される（形は秘密）。<br />
            ② 後手がカードを1枚選んで出す。<br />
            ③ 両カードをオープンし、じゃんけんで勝敗を判定。<br />
            ④ 勝者が点を獲得し、次ラウンドの先手になる。引き分けは後手が先手になる。
          </p>
        </div>

        <hr className="modal__divider" />

        <div className="modal__section">
          <div className="modal__section-title">勝利条件</div>
          <p className="modal__text">
            9ラウンド終了後、合計点数が多いほうが勝ちです。
          </p>
        </div>

        <button className="btn-primary modal__close" onClick={onClose}>
          閉じる
        </button>
      </div>
    </div>
  );
}

export default function App() {
  const [screen, setScreen]           = useState<Screen>('start');
  const [game, setGame]               = useState<GameView | null>(null);
  const [lastRound, setLastRound]     = useState<RoundRecord | null>(null);
  const [pendingGame, setPendingGame] = useState<GameView | null>(null);
  const [loading, setLoading]         = useState(false);
  const [error, setError]             = useState<string | null>(null);
  const [showRules, setShowRules]     = useState(false);

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
        {showRules && <RulesModal onClose={() => setShowRules(false)} />}
        <div className="start-screen">
          <h1 className="start-screen__title">三色じゃんけん</h1>
          <p className="start-screen__subtitle">
            グー・チョキ・パー × 白・赤・青　全9ラウンド制
          </p>
          {error && <div className="error-banner">{error}</div>}
          <div className="start-screen__btn-group">
            <button className="btn-primary" onClick={handleNewGame} disabled={loading}>
              {loading ? '準備中...' : 'ゲームスタート'}
            </button>
            <button className="btn-text" onClick={() => setShowRules(true)}>
              ゲームルールを確認する
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Game over screen ──────────────────────────────────────────────────────────

  if (screen === 'game_over' && game) {
    const winnerLabel =
      game.winner === 'human' ? 'あなたの勝利！'
      : game.winner === 'ai'  ? 'AIの勝利'
      : '引き分け';
    const cls = `game-over__result game-over__result--${game.winner ?? 'draw'}`;
    return (
      <div className="app">
        {showRules && <RulesModal onClose={() => setShowRules(false)} />}
        <div className="game-over">
          <div className={cls}>{winnerLabel}</div>
          <div className="game-over__score">
            あなた {game.human_score}点 <span>vs</span> AI {game.ai_score}点
          </div>
          <HistoryPanel history={game.history} />
          <div className="start-screen__btn-group">
            <button className="btn-primary" onClick={handleNewGame} disabled={loading}>
              もう一度プレイ
            </button>
            <button className="btn-text" onClick={() => setScreen('start')}>
              タイトルに戻る
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Playing / round_result ────────────────────────────────────────────────────

  if (!game) return null;

  const isMyTurn   = game.is_human_turn && screen === 'playing' && !loading;
  const sortedHand = sortHand(game.human_hand);

  return (
    <div className="app">
      {showRules && <RulesModal onClose={() => setShowRules(false)} />}

      {/* Round result overlay */}
      {screen === 'round_result' && lastRound && (
        <div className="round-result">
          <div className="round-result__box">
            <div className="round-result__title">ラウンド {lastRound.round_num} 結果</div>
            <div className="round-result__cards">
              <div className="battle-slot">
                <div className="battle-slot__label">
                  あなた（{lastRound.human_was_first ? '先手' : '後手'}）
                </div>
                <Card card={lastRound.human_card} />
              </div>
              <div className="battle-zone__vs">vs</div>
              <div className="battle-slot">
                <div className="battle-slot__label">
                  AI（{lastRound.human_was_first ? '後手' : '先手'}）
                </div>
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
          <div className="score-header__round">
            Round {game.round + 1} / 9
          </div>
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
        <div className="zone-label">AIの手札（{game.ai_card_count}枚）</div>
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
                <div className="battle-slot__label">AIのカード（色のみ公開）</div>
                <FaceDownCard colorHint={game.pending_color_name} />
              </div>
              <div className="battle-zone__vs">vs</div>
              <div className="battle-slot">
                <div className="battle-slot__label">あなたのカード（選択中）</div>
                <div className="card card--facedown" style={{ opacity: 0.25 }}>
                  <span className="card__back-mark">？</span>
                </div>
              </div>
            </>
          ) : (
            <div className="battle-zone__status">
              {game.is_human_first ? (
                <>
                  <strong>あなたが先手です</strong><br />
                  カードを1枚選んでください。<br />
                  <small>あなたのカードの「色」のみAIに公開されます</small>
                </>
              ) : loading ? (
                <span>AIが考えています…</span>
              ) : (
                <>
                  <strong>AIが先手です</strong><br />
                  AIのカードが伏せられたら、あなたの番です。
                </>
              )}
            </div>
          )}
        </div>

        {/* Human zone */}
        <hr className="divider" />
        <div className="human-zone">
          <div className="zone-label">あなたの手札（{sortedHand.length}枚）</div>
          <div className="human-hand">
            {sortedHand.map(card => (
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
              : screen === 'round_result'
              ? ''
              : ''}
          </div>
        </div>

        <hr className="divider" />
        <HistoryPanel history={game.history} />

        <div style={{ display: 'flex', gap: '12px', marginTop: '4px' }}>
          <button className="btn-secondary" onClick={handleNewGame} disabled={loading}>
            最初からやり直す
          </button>
          <button className="btn-text" onClick={() => setShowRules(true)}>
            ルール確認
          </button>
        </div>
      </div>
    </div>
  );
}
