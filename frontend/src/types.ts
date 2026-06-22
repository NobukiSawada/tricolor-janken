export interface CardData {
  id: number;
  shape: string;   // グー | チョキ | パー
  color: string;   // 白 | 青 | 赤
  points: number;  // 1 | 2 | 3
}

export interface RoundRecord {
  round_num: number;
  human_card: CardData;
  ai_card: CardData;
  human_was_first: boolean;
  result: 'human_win' | 'ai_win' | 'draw';
  human_points: number;
  ai_points: number;
}

export interface GameView {
  round: number;              // completed rounds (0-9)
  phase: 0 | 1;
  human_score: number;
  ai_score: number;
  human_hand: CardData[];
  ai_card_count: number;
  is_human_first: boolean;    // for current round
  is_human_turn: boolean;
  pending_color_name: string | null;  // color hint if AI played first
  history: RoundRecord[];
  is_terminal: boolean;
  winner: 'human' | 'ai' | 'draw' | null;
  ai_trained: boolean;
}
