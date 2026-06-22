# 進捗記録

## 2026-06-19 — Phase 1: AI学習環境（シミュレータ）の構築

### 完了内容

**ブランチ: `step1`**

#### `core/game.py` — ゲームエンジン
- カードを `shape * 3 + color` の整数 (0..8) でエンコード
- 手札を 9-bit ビットマスク整数で表現（コピーコスト最小化）
- `GameState` クラスを `__slots__` で実装（メモリ効率化）
  - `step(card)` : 現在プレイヤーがカードを出し、新しい状態を返す（不変操作）
  - `legal_actions()` : 合法手のリストを返す
  - `info_set_key()` : 現在プレイヤーの情報集合キーを文字列で返す
    - フェーズ1（後手の意思決定時）は相手カードの「色のみ」を情報として含む
- `is_terminal`, `utility(player)` でゲーム終了判定と効用計算

#### `core/cfr.py` — CFRソルバー
- **Vanilla CFR** (`train_vanilla`): ゲーム木を全探索。小規模テスト用
- **External Sampling MCCFR** (`train_mccfr`): 自プレイヤーの全行動を展開、相手行動はサンプリング。百万回規模の学習に対応
- `save` / `load` で学習済み重みを `.pkl` ファイルに保存・再開可能
- `action_probs(info_set_key, actions)` でナッシュ均衡近似の行動確率を取得

---

## 2026-06-22 — Phase 1 修正: Outcome Sampling MCCFR への変更

**ブランチ: `step2`**

#### `core/cfr.py` — MCCFRアルゴリズムの変更（External → Outcome Sampling）

- **変更前**: External Sampling MCCFR（更新プレイヤーのノードで全行動展開、相手ノードで1アクションサンプリング）
- **変更後**: Outcome Sampling MCCFR（更新プレイヤーのノードでも1アクションのみサンプリング）
  - 計算量が O(actions^depth) から O(game_depth) に改善
  - εグリーディ探索（ε=0.6）を導入し、全行動が確率的に探索されることを保証
  - reach確率（`pi_i`, `pi_neg`）を明示的に管理し、regret更新に重要度重みを適用
  - 進捗ログ間隔を 10,000 → 100,000 イテレーションに変更（出力頻度の最適化）

#### `core/train.py` — 学習エントリーポイント
- `python -m core.train` で即座に学習開始
- `--method`, `--iter`, `--load`, `--save`, `--quiet` オプション対応

#### `.gitignore` 更新
- `docs/requirements.md`（要件定義書）を除外済み
- `*.pkl`, `weights/`（学習重みファイル）を除外に追加

### 次フェーズの予定
- Phase 2: フロントエンド実装（UI）— スタック選定（Tauri/Flutter/PySide6 等）

---

## 2026-06-22 — Phase 2 開始: Tauri + React + TypeScript フロントエンド

**ブランチ: `step2`**

### フロントエンドスタック選定

- **Tauri + React + TypeScript** を採用
  - Reactでゲームロジックを表示、PythonバックエンドはFastAPI経由で連携
  - Rustが未インストールのため、現時点では Vite dev server + FastAPI 構成で開発
  - 将来的に Tauri でラップして `.exe` 化予定

### 実装内容

#### `api/main.py` — Python ↔ React 橋渡しサーバー (FastAPI)
- エンドポイント: `POST /api/new-game`, `POST /api/play`, `GET /api/state`
- 学習済み `weights.pkl` があれば CFR戦略を使用、なければランダムプレイにフォールバック
- AI のターンは自動進行（フロントエンドから呼び出す必要なし）
- `GameView` として人間視点の状態を返す（AI手札は枚数のみ、未公開部分は非表示）

#### `core/game.py` — 最小変更
- `history` タプルを `(fp_card, sp_card, result)` から `(fp_card, sp_card, result, first_player_idx)` に拡張
  - API側でラウンドの先手を特定するために必要
  - `info_set_key()` のエンコードは変更なし（既存学習重みと互換性維持）

#### `frontend/` — React + TypeScript UI
- `src/types.ts`: `CardData`, `RoundRecord`, `GameView` インターフェース定義
- `src/api.ts`: FastAPI クライアント（`/api` プレフィックスで Vite proxy 経由）
- `src/App.tsx`: ゲーム全体のステートマシン（start / playing / round_result / game_over）
- `src/components/Card.tsx`: カードコンポーネント（表面・裏面・色ヒント表示対応）
- `src/components/HistoryPanel.tsx`: 対戦履歴トグルパネル
- `vite.config.ts`: `/api` → `http://localhost:8000` のプロキシ設定追加

### 起動方法
```bash
# ターミナル1: Python API サーバー
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload

# ターミナル2: Vite dev server
cd frontend && npm run dev
# → http://localhost:5173 でゲームをプレイ可能
```

### 次フェーズの予定
- AIの学習: `python -m core.train` で `weights.pkl` を生成し、CFR戦略を有効化
- Tauri統合: Rust インストール後に `src-tauri/` を追加して `.exe` ビルド
