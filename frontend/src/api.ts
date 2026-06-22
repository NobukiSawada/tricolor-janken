import type { GameView } from './types';

async function request<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(path, {
    method: body !== undefined ? 'POST' : 'GET',
    headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? 'API error');
  }
  return res.json();
}

export const api = {
  newGame: () => request<GameView>('/api/new-game', {}),
  play: (cardId: number) => request<GameView>('/api/play', { card_id: cardId }),
  getState: () => request<GameView>('/api/state'),
};
