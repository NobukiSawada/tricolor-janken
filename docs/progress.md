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

#### `core/train.py` — 学習エントリーポイント
- `python -m core.train` で即座に学習開始
- `--method`, `--iter`, `--load`, `--save`, `--quiet` オプション対応

#### `.gitignore` 更新
- `docs/requirements.md`（要件定義書）を除外済み
- `*.pkl`, `weights/`（学習重みファイル）を除外に追加

### 次フェーズの予定
- Phase 2: フロントエンド実装（UI）— スタック選定（Tauri/Flutter/PySide6 等）
