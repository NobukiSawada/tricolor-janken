import type { CardData } from '../types';
import './Card.css';

const SHAPE_EMOJI: Record<string, string> = {
  'グー': '✊',
  'チョキ': '✌️',
  'パー': '🖐️',
};

const COLOR_CLASS: Record<string, string> = {
  '白': 'white',
  '青': 'blue',
  '赤': 'red',
};

interface CardProps {
  card: CardData;
  onClick?: () => void;
  disabled?: boolean;
  dimmed?: boolean;
}

export function Card({ card, onClick, disabled, dimmed }: CardProps) {
  const colorClass = COLOR_CLASS[card.color] ?? '';
  const isClickable = !!onClick && !disabled;

  return (
    <button
      className={`card card--${colorClass} ${isClickable ? 'card--clickable' : ''} ${dimmed ? 'card--dimmed' : ''}`}
      onClick={isClickable ? onClick : undefined}
      disabled={!isClickable}
      title={`${card.shape}${card.color} (${card.points}点)`}
    >
      <span className="card__emoji">{SHAPE_EMOJI[card.shape]}</span>
      <span className="card__name">{card.shape}</span>
      <span className="card__color">{card.color}</span>
      <span className="card__points">{card.points}pt</span>
    </button>
  );
}

interface FaceDownCardProps {
  colorHint?: string;  // show color name without revealing shape
}

export function FaceDownCard({ colorHint }: FaceDownCardProps) {
  const colorClass = colorHint ? COLOR_CLASS[colorHint] ?? '' : '';
  return (
    <div className={`card card--facedown ${colorHint ? `card--hint card--${colorClass}` : ''}`}>
      {colorHint ? (
        <>
          <span className="card__hint-label">色</span>
          <span className="card__hint-color">{colorHint}</span>
          <span className="card__hint-pts">
            {colorHint === '白' ? 1 : colorHint === '青' ? 2 : 3}pt
          </span>
        </>
      ) : (
        <span className="card__back-mark">？</span>
      )}
    </div>
  );
}
