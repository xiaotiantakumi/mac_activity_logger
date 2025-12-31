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
            # ただし、Windowタイトルだけ変わっている可能性もあるので要検討だが
            # ここでは「画面の見た目が変わらなければスキップ」とする
            # ★改善点: 音声がある場合は画像が変わってなくてもログに残したいかもしれない。
            # 今回は「画面ログに音声を付与する」方針なので、画面変化なしならログなしのままとする。
            return None

        # 3. 変化あり -> 詳細処理 (OCR & Window Info)
        # ここで初めて重い処理（OCR）を走らせる
        text = self.ocr.extract_text(image_ref)

        # 3.1 Text Similarity Check (Deduplication)
        # 画像が変わっていても、テキストがほぼ同じならスキップする (OCRノイズ対策)
        if self.similarity.is_text_similar(text, self.last_ocr_text):
            # 類似している場合はスキップ
            # ただし、状態(画像特徴量など)は更新しておくべきか？
            # ここでは「実質変化なし」とみなして、画像特徴量も最新に更新してループを継続させることで
            # 微妙な変化の蓄積によるスナップショット漏れを防ぐ
            self.last_img_feature = current_feature
            # テキストも最新の方が精度が良い可能性があるので更新
            self.last_ocr_text = text
            return None

        window_info = self.window.get_active_window_title()
        
        # 4. Entity作成
        screen_data = ScreenData(
            timestamp=now,
            ocr_text=text,
            window_title=window_info["title"],
            app_name=window_info["app"],
            feature_vector=None # 保存不要ならNone
        )
        
        entry = LogEntry(
            timestamp=now,
            screen=screen_data,
            audio_transcript=audio_transcript # 注入された音声テキスト
        )
        
        # 5. Save
        self.persistence.save(entry)
        
        # 6. Update State
        self.last_img_feature = current_feature
        self.last_ocr_text = text
        
        return entry
