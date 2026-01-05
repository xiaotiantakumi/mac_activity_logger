# macOS Activity Logger - プロジェクト概要

## プロジェクトの目的

macOS Activity Logger は、PyObjC を使用した軽量でローカル完結型の macOS アクティビティロガーです。画面の「見た目」が変化した時だけ、テキスト（OCR）とアクティブなウィンドウ名を記録し、さらに音声（Whisper）による文字起こしも行います。記録されたログは、ローカル LLM（Gemma）を使用して自動的に要約されます。

## 主要な特徴

- **ディスク負荷ゼロ**: スクリーンショットはメモリ上でのみ処理し、画像ファイルとして保存しません（SSD に優しい）
- **スマートな差分検知**: 画面に変化がない（画像および OCR テキストが類似している）場合は処理をスキップし、CPU 負荷を抑え、ログの重複を防ぎます
- **ローカル OCR**: macOS 標準の Vision Framework を使い、外部通信なしで高精度に日本語/英語を読み取ります
- **音声文字起こし**: mlx-whisper を使用してローカルで音声を文字起こしします
- **自動要約**: Gemma-2-2b-it-4bit を使用して、視覚的活動と音声活動を分離して要約します
- **JSONL 形式**: ログは構造化された JSONL 形式で保存され、プログラムでの解析が容易です

## アーキテクチャ

このプロジェクトは**Onion Architecture（クリーンアーキテクチャ）**に基づいて設計されています。

### レイヤー構造

```
src/logger/
├── domain/          # ドメイン層（ビジネスロジック）
├── application/     # アプリケーション層（ユースケース）
├── infrastructure/  # インフラ層（OS依存、外部ライブラリ）
├── presentation/    # プレゼンテーション層（CLI）
└── resources/       # リソース（プロンプトテンプレート）
```

### 各レイヤーの責務

#### Domain Layer (`domain/`)

- **entities.py**: ドメインエンティティ（`LogEntry`, `ScreenData`）
- **services.py**: ドメインサービス（`SimilarityChecker` - 画像・テキストの類似度判定）
- **interfaces.py**: ドメインインターフェース（`LlmProvider`）

#### Application Layer (`application/`)

- **use_cases.py**: メインユースケース（`ScreenMonitoringUseCase` - 画面監視のメインループ）
- **summarization_use_case.py**: 要約ユースケース（`LogSummarizationUseCase` - ログの自動要約）
- **interfaces.py**: アプリケーション層のインターフェース（`ScreenCaptureInterface`, `OcrInterface`, `WindowInfoInterface`, `PersistenceInterface`）

#### Infrastructure Layer (`infrastructure/`)

- **mac_os/**: macOS 固有の実装
  - `screen.py`: `ScreenCapturer` - Quartz を使用した画面キャプチャ
  - `vision.py`: `OcrService` - Vision Framework を使用した OCR
  - `accessibility.py`: `WindowInfoService` - Accessibility API を使用したウィンドウ情報取得
  - `audio.py`: 音声録音関連（現在は WhisperService に統合）
  - `media_loader.py`: PDF/画像ファイルの読み込み
- **ai/**: AI 関連の実装
  - `whisper_service.py`: `WhisperAudioService` - mlx-whisper を使用した音声文字起こし
  - `utils.py`: MLX 関連のユーティリティ（`mlx_lock` - Whisper と LLM の排他制御）
- **llm/**: LLM 関連の実装
  - `gemma_provider.py`: `GemmaLlmProvider` - mlx-lm を使用したローカル LLM
- **persistence/**: 永続化層
  - `jsonl_logger.py`: `JsonlLogger` - JSONL 形式でのログ保存

#### Presentation Layer (`presentation/`)

- **cli.py**: メイン CLI（`ActivityLoggerApp` - アクティビティロガーのエントリーポイント）
- **file_ocr_cli.py**: ファイル一括 OCR ツール
- **gemma_cli.py**: Gemma Chat CLI ツール

#### Resources (`resources/`)

- **prompts/**: LLM 要約用のプロンプトテンプレート
  - `summarize_visual_activity.txt`: 視覚的活動の要約プロンプト
  - `summarize_audio_activity.txt`: 音声活動の要約プロンプト
  - `summarize_daily_activity.txt`: 統合要約プロンプト

## 主要なコンポーネント

### 1. ScreenMonitoringUseCase

画面監視のメインロジックを担当します。

**処理フロー:**

1. 定期的に画面をキャプチャ
2. 前回フレームとの類似度を判定（画像・テキスト）
3. 変化がある場合のみ OCR を実行
4. アクティブウィンドウ情報を取得
5. 音声文字起こし結果を取得
6. `LogEntry`を作成して保存

**重要な設計:**

- 画像の類似度判定はリサイズされた画像（100x100）で行い、重い OCR 処理は変化がある場合のみ実行
- 音声がある場合は、画面変化がなくてもログに記録（ただし OCR テキストは空）

### 2. LogSummarizationUseCase

ログの自動要約を担当します。

**機能:**

- 視覚的活動（`visual`）と音声活動（`audio`）を分離して要約
- バックグラウンドスレッドで定期的にログをスキャン
- チャンク単位（デフォルト 10 件）で要約を生成
- 状態管理により、処理済みログを追跡

**出力ファイル:**

- `logs/YYYY-MM-DD/visual_summary.jsonl`: 視覚的活動の要約
- `logs/YYYY-MM-DD/audio_summary.jsonl`: 音声活動の要約
- `logs/YYYY-MM-DD/summary.jsonl`: 統合要約（未使用）

### 3. WhisperAudioService

音声の文字起こしを担当します。

**処理フロー:**

1. `sounddevice`を使用してマイクから音声を録音
2. 5 秒チャンクでキューに蓄積
3. 10 秒分が蓄積されたら Whisper で文字起こし
4. VAD（Voice Activity Detection）で無音をフィルタ
5. ハルシネーション（繰り返しパターン、既知のフレーズ）をフィルタ
6. 文字起こし結果をバッファに保存

**重要な設計:**

- `mlx_lock`を使用して Gemma LLM との排他制御を実現
- バックグラウンドスレッドで非同期処理

### 4. GemmaLlmProvider

ローカル LLM を使用した要約生成を担当します。

**機能:**

- `mlx-lm`を使用してローカルで LLM 推論
- プロンプトテンプレートから要約プロンプトを生成
- JSON 形式のレスポンスをパース

**重要な設計:**

- `mlx_lock`を使用して Whisper との排他制御を実現
- チャットテンプレートに対応

### 5. SimilarityChecker

画像・テキストの類似度判定を担当します。

**画像類似度:**

- リサイズされた画像（100x100）の平均差分を計算
- 閾値（デフォルト 95%）以上の類似度であれば「変化なし」と判定

**テキスト類似度:**

- `difflib.SequenceMatcher`を使用
- 閾値（デフォルト 0.8）以上の類似度であれば「類似」と判定

## データフロー

### メインループ（cli.py）

```
1. ActivityLoggerApp初期化
   ├─ 各種サービス初期化（Screen, OCR, Window, Audio, Persistence, Similarity）
   ├─ ScreenMonitoringUseCase作成
   └─ LogSummarizationUseCase作成（視覚・音声それぞれ）

2. 音声サービス開始
   ├─ WhisperAudioService.preload_model() - モデル事前読み込み
   └─ WhisperAudioService.start_recording() - 録音開始（バックグラウンドスレッド）

3. 要約スレッド開始
   ├─ LogSummarizationUseCase.start_monitoring() - 視覚的要約スレッド
   └─ LogSummarizationUseCase.start_monitoring() - 音声要約スレッド

4. メインループ（monitoring_loop）
   while not should_stop:
     ├─ WhisperAudioService.get_transcript_chunk() - 音声文字起こし結果取得
     ├─ ScreenMonitoringUseCase.execute_step() - 画面監視ステップ実行
     │   ├─ 画面キャプチャ
     │   ├─ 類似度判定
     │   ├─ OCR（変化がある場合のみ）
     │   ├─ ウィンドウ情報取得
     │   └─ LogEntry保存
     └─ インターバル待機
```

### 要約フロー（LogSummarizationUseCase）

```
1. バックグラウンドスレッドで定期的にスキャン
   ├─ logs/YYYY-MM-DD/activity.jsonlを読み込み
   ├─ 処理済み行数を状態ファイルから取得
   └─ 未処理のエントリを取得

2. エントリのフィルタリング
   ├─ visual: is_screen_change=trueのエントリのみ
   └─ audio: transcriptが空でないエントリのみ

3. チャンク単位で要約生成
   ├─ プロンプトテンプレートを読み込み
   ├─ ログエントリをフォーマット
   ├─ GemmaLlmProvider.process_content()で要約生成
   └─ visual_summary.jsonl / audio_summary.jsonlに保存

4. 状態更新
   └─ 処理済み行数を状態ファイルに保存
```

## データ構造

### LogEntry

```python
@dataclass
class LogEntry:
    timestamp: datetime
    screen: ScreenData
    audio_transcript: str = ""
    metadata: Dict[str, Any] = {}
```

### ScreenData

```python
@dataclass
class ScreenData:
    timestamp: datetime
    image_data: Optional[bytes] = None
    ocr_text: str = ""
    window_title: str = ""
    app_name: str = ""
    feature_vector: Any = None
```

### ログファイル形式（JSONL）

**activity.jsonl:**

```json
{
  "timestamp": "2025-12-30T20:25:27.779423",
  "screen": {
    "ocr_text": "ファイル 編集 選択 表示...",
    "window_title": "mac_activity_logger - VS Code",
    "app_name": "Code"
  },
  "audio": {
    "transcript": "こんにちは"
  },
  "metadata": {
    "is_screen_change": true
  }
}
```

**visual_summary.jsonl / audio_summary.jsonl:**

```json
{
  "timestamp_start": "2025-12-30T20:00:00",
  "timestamp_end": "2025-12-30T20:10:00",
  "summary": "ユーザーはVS Codeでコードを編集していました..."
}
```

## 技術スタック

### コアライブラリ

- **PyObjC**: macOS API へのアクセス
  - `pyobjc-framework-quartz`: 画面キャプチャ
  - `pyobjc-framework-vision`: OCR
  - `pyobjc-framework-applicationservices`: アクセシビリティ API
  - `pyobjc-framework-avfoundation`: メディア処理
  - `pyobjc-framework-speech`: 音声認識（未使用、Whisper を使用）

### AI/ML ライブラリ

- **mlx**: Apple Silicon 向け機械学習フレームワーク
- **mlx-whisper**: Whisper モデルの MLX 実装
- **mlx-lm**: LLM モデルの MLX 実装
- **numpy**: 数値計算
- **numba**: 高速化

### その他

- **sounddevice**: 音声録音
- **safetensors**: モデル読み込み

## 依存関係と制約

### システム要件

- macOS (Apple Silicon 推奨) - mlx-whisper のために M1/M2/M3/M4 チップが強く推奨
- Python 3.12+
- `portaudio` (brew install portaudio)

### 必要な権限

- **画面収録 (Screen Recording)**: スクリーンショットのために必要
- **アクセシビリティ (Accessibility)**: ウィンドウ情報取得のために必要
- **マイク (Microphone)**: 音声録音のために必要

### モデルダウンロード

初回使用前に以下のモデルをダウンロードする必要があります：

- `mlx-community/whisper-large-v3-turbo`: 音声文字起こし用
- `mlx-community/gemma-2-2b-it-4bit`: 要約生成用

```bash
uv run scripts/download_model.py
```

## 重要な設計パターン

### 1. 依存性逆転の原則

- アプリケーション層はインターフェースに依存し、実装はインフラ層に存在
- 例: `ScreenMonitoringUseCase`は`ScreenCaptureInterface`に依存し、`ScreenCapturer`はその実装

### 2. 排他制御

- `mlx_lock`を使用して Whisper と Gemma LLM の同時実行を防止
- Apple Silicon の Metal コンテキストの競合を回避

### 3. 状態管理

- `LogSummarizationUseCase`は`summarizer_state_{type}.json`で処理済み行数を追跡
- 日付ごとに状態を管理

### 4. 非同期処理

- 音声文字起こし: バックグラウンドスレッドで録音・文字起こし
- 要約生成: バックグラウンドスレッドで定期的にスキャン・要約

### 5. リソース効率化

- 画像はメモリ上でのみ処理（ディスクに保存しない）
- 類似度判定はリサイズ画像（100x100）で実行
- 変化がない場合は重い OCR 処理をスキップ

## ファイル構造の詳細

```
src/logger/
├── domain/
│   ├── entities.py          # LogEntry, ScreenData
│   ├── services.py          # SimilarityChecker
│   └── interfaces.py        # LlmProvider
├── application/
│   ├── use_cases.py         # ScreenMonitoringUseCase
│   ├── summarization_use_case.py  # LogSummarizationUseCase
│   └── interfaces.py        # ScreenCaptureInterface, OcrInterface, etc.
├── infrastructure/
│   ├── mac_os/
│   │   ├── screen.py        # ScreenCapturer
│   │   ├── vision.py        # OcrService
│   │   ├── accessibility.py # WindowInfoService
│   │   ├── audio.py         # (未使用、WhisperServiceに統合)
│   │   └── media_loader.py  # PDF/画像読み込み
│   ├── ai/
│   │   ├── whisper_service.py  # WhisperAudioService
│   │   └── utils.py         # mlx_lock
│   ├── llm/
│   │   └── gemma_provider.py   # GemmaLlmProvider
│   └── persistence/
│       └── jsonl_logger.py  # JsonlLogger
├── presentation/
│   ├── cli.py               # ActivityLoggerApp (メインCLI)
│   ├── file_ocr_cli.py      # ファイル一括OCRツール
│   └── gemma_cli.py         # Gemma Chat CLI
└── resources/
    └── prompts/
        ├── summarize_visual_activity.txt
        ├── summarize_audio_activity.txt
        └── summarize_daily_activity.txt
```

## 主要な設定とオプション

### CLI オプション（cli.py）

- `--interval`: チェック間隔（秒、デフォルト: 2.0）
- `--threshold`: 変化検知の感度（%、デフォルト: 95.0）
- `--logs-dir`: ログの保存先（デフォルト: `logs`）
- `--no-audio`: 音声記録を無効化
- `--summarize`: 要約機能を有効化（デフォルト: 有効）
- `--summary-chunk-size`: 要約を実行するログエントリの単位（デフォルト: 10）

### WhisperAudioService 設定

- `model_path`: デフォルト `"mlx-community/whisper-large-v3-turbo"`
- `sample_rate`: デフォルト `16000`
- `vad_threshold`: VAD 閾値（デフォルト: 0.015）
- `min_seconds_to_transcribe`: 文字起こし実行までの最小秒数（デフォルト: 10.0）

### GemmaLlmProvider 設定

- `model_id`: デフォルト `"mlx-community/gemma-2-2b-it-4bit"`
- `max_tokens`: デフォルト `2048`

## エラーハンドリング

### 権限エラー

- 画面収録・アクセシビリティ・マイクの権限がない場合、機能が制限されます
- ウィンドウ名が`Unknown`、OCR が空になる可能性があります

### モデル読み込みエラー

- Whisper/Gemma モデルの読み込みに失敗した場合、該当機能は無効化されます
- エラーメッセージが表示されますが、他の機能は継続して動作します

### ハルシネーションフィルタ

- Whisper の文字起こし結果から、繰り返しパターンや既知のフレーズをフィルタ
- `_is_hallucination()`メソッドで判定

## 拡張ポイント

### 新しい要約タイプの追加

1. `resources/prompts/`に新しいプロンプトテンプレートを追加
2. `LogSummarizationUseCase._is_entry_relevant()`にフィルタロジックを追加
3. `cli.py`で新しい`LogSummarizationUseCase`インスタンスを作成

### 新しい LLM プロバイダーの追加

1. `domain/interfaces.py`の`LlmProvider`インターフェースを実装
2. `infrastructure/llm/`に新しいプロバイダーを追加
3. `LogSummarizationUseCase`で使用

### 新しい永続化方法の追加

1. `application/interfaces.py`の`PersistenceInterface`を実装
2. `infrastructure/persistence/`に新しい実装を追加
3. `ScreenMonitoringUseCase`で使用

## ログファイルの場所

- **アクティビティログ**: `logs/YYYY-MM-DD/activity.jsonl`
- **視覚的要約**: `logs/YYYY-MM-DD/visual_summary.jsonl`
- **音声要約**: `logs/YYYY-MM-DD/audio_summary.jsonl`
- **要約状態**: `logs/summarizer_state_visual.json`, `logs/summarizer_state_audio.json`
- **システムログ**: `logs/system_summarizer.log`

## 実行方法

### メインロガーの起動

```bash
uv run src/logger/presentation/cli.py
```

### ファイル一括 OCR

```bash
uv run src/logger/presentation/file_ocr_cli.py --input-dir /path/to/files
```

### Gemma Chat

```bash
uv run src/logger/presentation/gemma_cli.py -i
```
