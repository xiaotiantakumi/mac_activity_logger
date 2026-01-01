import time
from datetime import datetime
from typing import Optional
import numpy as np

from ..domain.entities import LogEntry, ScreenData
from ..domain.services import SimilarityChecker
from .interfaces import ScreenCaptureInterface, OcrInterface, WindowInfoInterface, PersistenceInterface

class ScreenMonitoringUseCase:
    """
    画面監視のメインループロジック。
    定期的(interval)に画面を見て、変化があればOCRして保存する。
    """
    
    def __init__(
        self,
        screen_service: ScreenCaptureInterface,
        ocr_service: OcrInterface,
        window_service: WindowInfoInterface,
        persistence_service: PersistenceInterface,
        similarity_service: SimilarityChecker
    ):
        self.screen = screen_service
        self.ocr = ocr_service
        self.window = window_service
        self.persistence = persistence_service
        self.similarity = similarity_service
        
        # 前回フレームの状態保持
        self.last_img_feature: Optional[np.ndarray] = None
        self.last_ocr_text: Optional[str] = None
        
    def execute_step(self, audio_transcript: str = "") -> Optional[LogEntry]:
        """
        1ステップ実行する。
        変化があればLogEntryを返し、かつ保存する。
        変化がなければNoneを返す。
        """
        now = datetime.now()
        
        # 1. Capture
        image_ref = self.screen.capture_screen()
        if image_ref is None:
            return None

        # 2. Similarity Check
        # 比較用画像を作成 (インフラ層の責務でnumpy化)
        current_feature = self.screen.resize_for_comparison(image_ref)
        
        if self.similarity.is_similar(current_feature, self.last_img_feature):
            # 変化なし -> スキップ
            # ただし、音声がある場合はログに残す。
            if not audio_transcript:
                return None
            
            # 音声がある場合は、画面変化がなくても通過させる。
            # ただし、OCRを毎回やるのは重いので、前回のOCR結果を使い回す手もあるが、
            # ここではシンプルに「通過」させて、この後のロジックに委ねる。
            # もしOCR負荷が気になるなら、OCR処理の手前で分岐が必要。

        # 3. 変化あり OR 音声あり -> 詳細処理 (OCR & Window Info)
        # ここで初めて重い処理（OCR）を走らせる
        text = self.ocr.extract_text(image_ref)

        # 類似度判定
        visual_similar = self.similarity.is_similar(current_feature, self.last_img_feature)
        text_similar = self.similarity.is_text_similar(text, self.last_ocr_text)
        
        # 画面としての変化があったか
        is_screen_change = not visual_similar or not text_similar

        # 3.1 変化なしの場合
        if not is_screen_change:
            # 音声がない場合はスキップ
            if not audio_transcript:
                self.last_img_feature = current_feature
                self.last_ocr_text = text
                return None
            
            # 音声がある場合は保存するが、OCRテキストは空にして冗長さを排除する
            log_text = ""
        else:
            # 変化ありの場合はOCRテキストを保持
            log_text = text

        window_info = self.window.get_active_window_title()
        
        # 4. Entity作成
        screen_data = ScreenData(
            timestamp=now,
            ocr_text=log_text, # 変化なしなら空
            window_title=window_info["title"],
            app_name=window_info["app"],
            feature_vector=None # 保存不要ならNone
        )
        
        entry = LogEntry(
            timestamp=now,
            screen=screen_data,
            audio_transcript=audio_transcript,
            metadata={"is_screen_change": is_screen_change}
        )
        
        # 5. Save
        self.persistence.save(entry)
        
        # 6. Update State
        # 状態更新には「本来のOCRテキスト(text)」を使い、次回の比較に備える
        self.last_img_feature = current_feature
        self.last_ocr_text = text
        
        return entry
