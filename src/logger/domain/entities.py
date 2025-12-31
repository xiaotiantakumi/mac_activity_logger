from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class ScreenData:
    """スクリーンショットに関連するデータ"""
    timestamp: datetime
    image_data: Optional[bytes] = None  # 生の画像データ（必要に応じて）
    ocr_text: str = ""
    window_title: str = ""
    app_name: str = ""
    
    # 比較用の特徴量（リサイズされた画像データなど）
    # numpy arrayは直接持たせず、bytesやlistで持つか、
    # 処理中にのみ保持するようにしてメモリ効率を上げる設計も可。
    # ここではシンプルに保持する（インフラ層で変換してセットする想定）
    feature_vector: Any = None 

@dataclass
class LogEntry:
    """1つのアクティビティログエントリ"""
    timestamp: datetime
    screen: ScreenData
    audio_transcript: str = ""
    
    # メタデータ (例: ユーザー、デバイスIDなど)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """永続化用"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "screen": {
                "ocr_text": self.screen.ocr_text,
                "window_title": self.screen.window_title,
                "app_name": self.screen.app_name,
            },
            "audio": {
                "transcript": self.audio_transcript
            },
            "metadata": self.metadata
        }
