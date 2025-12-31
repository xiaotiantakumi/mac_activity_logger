# macOS Activity Logger

PyObjC を使用した、軽量でローカル完結型の macOS アクティビティロガーです。
画面の「見た目」が変化した時だけ、テキスト（OCR）とアクティブなウィンドウ名を記録します。

## 特徴

- **ディスク負荷ゼロ**: スクリーンショットはメモリ上でのみ処理し、画像ファイルとして保存しません（SSD に優しい）。
- **スマートな差分検知**: 画面に変化がない場合は処理をスキップし、CPU 負荷を抑えます。
- **ローカル OCR**: macOS 標準の Vision Framework を使い、外部通信なしで高精度に日本語/英語を読み取ります。
- **JSONL 形式**: ログは構造化された JSONL 形式で保存され、プログラムでの解析が容易です。

## 必要要件

- macOS (Apple Silicon 推奨) -- **mlx-whisper** のために M1/M2/M3 チップが強く推奨されます。
- Python 3.12+ (uv で管理)
- **システム依存ライブラリ**: `portaudio` (マイク入力用)
  ```bash
  brew install portaudio
  ```
- **権限**: 画面収録 (Screen Recording), アクセシビリティ (Accessibility), マイク (Microphone)

## インストール

このプロジェクトは `uv` で管理されています。

```bash
# 依存関係のインストール
uv sync
```

## 使い方（動作確認）

### 1. ロガーの起動

以下のコマンドで監視を開始します。

```bash
uv run src/logger/presentation/cli.py
```

**一度実行した後、すぐに `Ctrl+C` で止めても構いません。**
初回実行時は、macOS から権限の許可を求めるポップアップが表示される場合があります。

#### オプション引数

- `--interval`: チェック間隔（秒）。デフォルトは `2.0`。
- `--threshold`: 変化検知の感度（％）。デフォルトは `95.0`。これより類似度が高ければスキップします。
- `--logs-dir`: ログの保存先。デフォルトは `logs`。

### 2. 権限の設定（重要）

**ログのウィンドウ名が `Unknown` になったり、OCR が空の場合は権限を確認してください。**

1. **システム設定** > **プライバシーとセキュリティ** を開く。
2. **画面収録 (Screen Recording)**:
   - ターミナル（または VS Code/Cursor）を許可してください。
3. **アクセシビリティ (Accessibility)**:
   - ターミナル（または VS Code/Cursor）を許可してください。
   - **注意**: すでにチェックが入っているのに動かない場合、一度リストから削除（➖ ボタン）して、再度追加（➕ ボタン）し、**アプリを再起動**してください。

### 3. ログの確認

`logs` ディレクトリに日付ごとのファイルが生成されます。

```bash
cat logs/activity_YYYY-MM-DD.jsonl
```

### 4. ファイル一括 OCR（PDF/画像対応）

指定したディレクトリ内のメディアファイル（PDF, JPEG, PNG 等）を一括で OCR し、テキストとして保存するツールも利用できます。

```bash
# デフォルトで data ディレクトリを処理
uv run src/logger/presentation/file_ocr_cli.py

# または任意のディレクトリを指定
uv run src/logger/presentation/file_ocr_cli.py --input-dir /path/to/files

# 出力先を指定する場合（デフォルトは input_dir/ocr_result）
uv run src/logger/presentation/file_ocr_cli.py --output-dir /path/to/output
```

OCR 結果は、指定した出力ディレクトリ（デフォルトの場合は `ocr_result`）に `.txt` ファイルとして保存されます。

**ログの例**:

```json
{
  "timestamp": "2025-12-30T20:25:27.779423",
  "screen": {
    "ocr_text": "ファイル 編集 選択 表示...",
    "window_title": "mac_activity_logger - VS Code",
    "app_name": "Code"
  },
  "audio": { "transcript": "" },
  "metadata": {}
}
```

## アーキテクチャ

Onion Architecture に基づき、OS 依存部分を分離しています。

- **Domain**: 純粋なロジック（Entities, 類似度判定）。
- **Application**: ユースケース（監視ループの制御）。
- **Infrastructure**: PyObjC を使った macOS API 呼び出し（Quartz, Vision, Accessibility）。
- **Presentation**: CLI エントリーポイント。
