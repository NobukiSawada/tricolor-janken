# tricolor-janken

**日本語** | [English](#english)

---

不完全情報カードゲーム「三色じゃんけん」をプレイできるモダンなデスクトップアプリケーション。
CFR（反事実後悔最小化）で学習した、数学的に最強のAIを搭載。

## ディレクトリ構成

```
tricolor-janken/
├── core/           # Pythonシミュレータ & CFR学習ロジック
│   ├── game.py     # カードエンコード・GameState・情報集合
│   ├── cfr.py      # Vanilla CFR + External Sampling MCCFR
│   └── train.py    # 学習エントリーポイント
├── frontend/       # UI（Tauri / Flutter / PySide6 — Phase 2）
├── docs/           # 進捗記録
└── README.md
```

## AI学習（Phase 1）

Python 3.9 以上が必要。外部ライブラリ不要（標準ライブラリのみ）。

```bash
# デフォルト: External Sampling MCCFR、100 000 イテレーション
python -m core.train

# チェックポイントから再開
python -m core.train --load weights.pkl --iter 500000

# Vanilla CFR（ゲーム木全探索 — テスト用）
python -m core.train --method vanilla --iter 500
```

学習済み重みは `weights.pkl` に保存されます（バージョン管理対象外）。

---

<a name="english"></a>

**[日本語](#tricolor-janken)** | English

---

A modern desktop application for **Tricolor Rock-Paper-Scissors (三色じゃんけん)**, an incomplete information card game.
Features a mathematically unbeatable AI trained via CFR (Counterfactual Regret Minimization).

## Project structure

```
tricolor-janken/
├── core/           # Python simulator & CFR learning logic
│   ├── game.py     # Card encoding, GameState, information set
│   ├── cfr.py      # Vanilla CFR + External Sampling MCCFR
│   └── train.py    # Training entry point
├── frontend/       # UI (Tauri / Flutter / PySide6 — Phase 2)
├── docs/           # Progress log
└── README.md
```

## AI Training (Phase 1)

Requires Python 3.9+.  No external dependencies beyond the standard library.

```bash
# Default: External Sampling MCCFR, 100 000 iterations
python -m core.train

# Continue training from a saved checkpoint
python -m core.train --load weights.pkl --iter 500000

# Vanilla CFR (exhaustive tree traversal — for testing only)
python -m core.train --method vanilla --iter 500
```

Trained weights are saved as `weights.pkl` (excluded from version control).
