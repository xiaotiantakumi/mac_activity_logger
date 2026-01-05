import threading
import time
from datetime import datetime
from typing import Optional, Callable, List

from ..infrastructure.mac_os.screen import ScreenCapturer
from ..infrastructure.mac_os.vision import OcrService
from ..infrastructure.mac_os.accessibility import WindowInfoService
from ..infrastructure.ai.whisper_service import WhisperAudioService
from ..infrastructure.persistence.jsonl_logger import JsonlLogger
from ..domain.services import SimilarityChecker
from .use_cases import ScreenMonitoringUseCase
from ..infrastructure.llm.gemma_provider import GemmaLlmProvider
from .summarization_use_case import LogSummarizationUseCase

class ActivityLoggerController:
    """
    アプリケーションのメインコントローラー。
    各種サービスの初期化、依存性注入、および監視ループのライフサイクルを管理します。
    Presentation層 (CLI/GUI) から呼び出されることを想定しています。
    """
    def __init__(
        self,
        interval: float = 2.0,
        threshold: float = 95.0,
        logs_dir: str = "logs",
        no_audio: bool = False,
        no_summarize: bool = False,
        summary_chunk_size: int = 10,
        lazy_init: bool = False
    ):
        self.interval = interval
        self.threshold = threshold
        self.logs_dir = logs_dir
        self.no_audio = no_audio
        self.no_summarize = no_summarize
        self.summary_chunk_size = summary_chunk_size
        
        self.should_stop = False
        self.is_running = False
        
        # コールバック (UI更新用)
        self.on_log_entry: Optional[Callable[[any], None]] = None
        self.on_status_change: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_summary: Optional[Callable[[str, str], None]] = None # type, summary_text

        # インフラ・アプリケーションレイヤーの初期化
        if not lazy_init:
            self.setup_ai_services()
            self.setup_os_services()

    def setup_ai_services(self):
        """
        重いAIモデルのロードなど、バックグラウンドスレッドで実行可能な初期化処理。
        """
        if self.no_audio:
            self.audio_service = None
        else:
            self.audio_service = WhisperAudioService()

        self.visual_summarizer = None
        self.audio_summarizer = None
        
        if not self.no_summarize:
            try:
                llm = GemmaLlmProvider()
                self.visual_summarizer = LogSummarizationUseCase(
                    llm_provider=llm,
                    summary_type="visual",
                    logs_root_dir=self.logs_dir
                )
                self.audio_summarizer = LogSummarizationUseCase(
                    llm_provider=llm,
                    summary_type="audio",
                    logs_root_dir=self.logs_dir
                )
                
                # Wire callbacks
                self.visual_summarizer.on_summary_generated = lambda s: self._handle_summary("visual", s)
                self.audio_summarizer.on_summary_generated = lambda s: self._handle_summary("audio", s)
            except Exception as e:
                self._notify_error(f"Failed to initialize summarization: {e}")

    def setup_os_services(self):
        """
        ScreenCapturerやWindowInfoServiceなど、OS依存（メインスレッド推奨）の初期化処理。
        """
        self.screen_service = ScreenCapturer()
        self.ocr_service = OcrService()
        self.window_service = WindowInfoService()
        self.persistence_service = JsonlLogger(output_dir=self.logs_dir)
        self.similarity_service = SimilarityChecker(threshold_percent=self.threshold)
        
        self.use_case = ScreenMonitoringUseCase(
            screen_service=self.screen_service,
            ocr_service=self.ocr_service,
            window_service=self.window_service,
            persistence_service=self.persistence_service,
            similarity_service=self.similarity_service
        )

    def _handle_summary(self, summary_type: str, summary_data: dict):
        if self.on_summary:
            self.on_summary(summary_type, summary_data.get("summary", ""))

    def _notify_status(self, status: str):
        if self.on_status_change:
            self.on_status_change(status)

    def _notify_error(self, error: str):
        if self.on_error:
            self.on_error(error)

    def _monitoring_loop(self):
        self._notify_status("Running")
        while not self.should_stop:
            start_time = time.time()
            try:
                transcript = ""
                if self.audio_service:
                    transcript = self.audio_service.get_transcript_chunk()
                
                entry = self.use_case.execute_step(audio_transcript=transcript)
                
                if entry and self.on_log_entry:
                    self.on_log_entry(entry)
                    
            except Exception as e:
                self._notify_error(f"Error in monitoring loop: {e}")
            
            elapsed = time.time() - start_time
            sleep_time = max(0, self.interval - elapsed)
            time.sleep(sleep_time)
        
        self._notify_status("Stopped")
        self.is_running = False

    def start(self):
        if self.is_running:
            return
        
        self.should_stop = False
        self.is_running = True
        
        # 1. Preload & Start Audio
        if self.audio_service:
            self.audio_service.preload_model()
            try:
                self.audio_service.start_recording()
            except Exception as e:
                self._notify_error(f"Failed to start audio service: {e}")

        # 2. Start Summarization
        if self.visual_summarizer:
            threading.Thread(
                target=self.visual_summarizer.start_monitoring,
                args=(self.summary_chunk_size,),
                daemon=True
            ).start()
        
        if self.audio_summarizer:
            threading.Thread(
                target=self.audio_summarizer.start_monitoring,
                args=(self.summary_chunk_size,),
                daemon=True
            ).start()

        # 3. Start Monitoring Loop in Background Thread
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()

    def stop(self):
        self.should_stop = True
        if self.audio_service:
            self.audio_service.stop_recording()
        if self.visual_summarizer:
            self.visual_summarizer.stop()
        if self.audio_summarizer:
            self.audio_summarizer.stop()
