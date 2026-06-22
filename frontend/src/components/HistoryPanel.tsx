import { useState } from 'react';
import type { RoundRecord } from '../types';
import './HistoryPanel.css';

const RESULT_LABEL: Record<string, string> = {
  human_win: 'あなたの勝ち',
  ai_win:    'AIの勝ち',
  draw:      'あいこ',
};

interface Props {
  history: RoundRecord[];
}

export function HistoryPanel({ history }: Props) {
  const [open, setOpen] = useState(false);

  if (history.length === 0) return null;

  return (
    <div className="history">
      <button className="history__toggle" onClick={() => setOpen(o => !o)}>
        対戦履歴 ({history.length}ラウンド) {open ? '▲' : '▼'}
      </button>
      {open && (
        <div className="history__list">
          {[...history].reverse().map(r => (
            <div key={r.round_num} className={`history__row history__row--${r.result}`}>
              <span className="history__round">R{r.round_num}</span>
              <span className="history__card">
                {r.human_was_first ? '先' : '後'} {r.human_card.shape}{r.human_card.color}
                {r.human_points > 0 && <span className="history__pts">+{r.human_points}</span>}
              </span>
              <span className="history__vs">vs</span>
              <span className="history__card">
                {!r.human_was_first ? '先' : '後'} {r.ai_card.shape}{r.ai_card.color}
                {r.ai_points > 0 && <span className="history__pts">+{r.ai_points}</span>}
              </span>
              <span className="history__result">{RESULT_LABEL[r.result]}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
