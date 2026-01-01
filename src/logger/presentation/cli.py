import sys
import time
import argparse
import signal
import threading
from datetime import datetime

# srcをパスに追加 (パッケージとしてインストールされていない場合用)
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

from src.logger.infrastructure.mac_os.screen import ScreenCapturer
from src.logger.infrastructure.mac_os.vision import OcrService
from src.logger.infrastructure.mac_os.accessibility import WindowInfoService
from src.logger.infrastructure.ai.whisper_service import WhisperAudioService  # Updated
from src.logger.infrastructure.persistence.jsonl_logger import JsonlLogger
from src.logger.domain.services import SimilarityChecker
from src.logger.application.use_cases import ScreenMonitoringUseCase
from src.logger.infrastructure.llm.gemma_provider import GemmaLlmProvider
from src.logger.application.summarization_use_case import LogSummarizationUseCase

class ActivityLoggerApp:
    def __init__(self, args):
        self.args = args
        self.should_stop = False
        
        # Initialize Services
        print("Initializing services...")
        self.screen_service = ScreenCapturer()
        self.ocr_service = OcrService()
        self.window_service = WindowInfoService()
        
        if getattr(args, "no_audio", False):
            print("Audio recording is disabled.")
            self.audio_service = None
        else:
            self.audio_service = WhisperAudioService()  # Use Whisper
        
        self.persistence_service = JsonlLogger(output_dir=args.logs_dir)
        self.similarity_service = SimilarityChecker(threshold_percent=args.threshold)
        
        self.use_case = ScreenMonitoringUseCase(
            screen_service=self.screen_service,
            ocr_service=self.ocr_service,
            window_service=self.window_service,
            persistence_service=self.persistence_service,
            similarity_service=self.similarity_service
        )

        # Summarization Setup
        self.visual_summarizer = None
        self.audio_summarizer = None
        
        if not getattr(args, "no_summarize", False):
            print("Summarization is ENABLED (Visual & Audio separated).")
            try:
                llm = GemmaLlmProvider()
                self.visual_summarizer = LogSummarizationUseCase(
                    llm_provider=llm,
                    summary_type="visual",
                    logs_root_dir=args.logs_dir
                )
                self.audio_summarizer = LogSummarizationUseCase(
                    llm_provider=llm,
                    summary_type="audio",
                    logs_root_dir=args.logs_dir
                )
            except Exception as e:
                print(f"⚠️ Failed to initialize summarization: {e}")
                self.visual_summarizer = None
                self.audio_summarizer = None
        else:
            print("Summarization is DISABLED.")

    def monitoring_loop(self):
        """
        Main Loop for Screen Monitoring.
        """
        print(f"Starting monitoring loop (Interval: {self.args.interval}s, Threshold: {self.args.threshold}%)")
        print(f"Logs will be saved to: {self.args.logs_dir}")
        print("Press Ctrl+C to stop.")
        
        while not self.should_stop:
            start_time = time.time()
            
            try:
                # 1. 音声テキストの取得 (非同期スレッドが解析した結果を回収)
                transcript = ""
                if self.audio_service:
                    transcript = self.audio_service.get_transcript_chunk()
                
                # 2. UseCase 実行
                entry = self.use_case.execute_step(audio_transcript=transcript)
                
                if entry:
                    # ログ出力 (Console)
                    status = "Screen Change" if entry.metadata.get("is_screen_change") else "Static"
                    print(f"[{entry.timestamp.strftime('%H:%M:%S')}] [{status}] {entry.screen.app_name} - {entry.screen.window_title[:30]}...")
                    if transcript:
                        print(f"  > Audio: {transcript}")
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
            
            elapsed = time.time() - start_time
            sleep_time = max(0, self.args.interval - elapsed)
            time.sleep(sleep_time)

    def run(self):
        # 0. Preload Model (Download & Warmup)
        if self.audio_service:
            self.audio_service.preload_model()

        # 1. Start Audio Service
        if self.audio_service:
            try:
                self.audio_service.start_recording()
            except Exception as e:
                print(f"Failed to start audio service: {e}")
                print("Continuing without audio log...")

        # 2. Start Summarization Threads
        if self.visual_summarizer:
            print(f"Starting visual summarization thread (chunk_size={self.args.summary_chunk_size})...")
            threading.Thread(
                target=self.visual_summarizer.start_monitoring,
                args=(self.args.summary_chunk_size,),
                daemon=True
            ).start()

        if self.audio_summarizer:
            print(f"Starting audio summarization thread (chunk_size={self.args.summary_chunk_size})...")
            threading.Thread(
                target=self.audio_summarizer.start_monitoring,
                args=(self.args.summary_chunk_size,),
                daemon=True
            ).start()

        # 3. Run Monitoring Loop (Blocking)
        try:
            self.monitoring_loop()
        except KeyboardInterrupt:
            pass
        finally:
            self.should_stop = True
            print("\nStopping logger...")
            if self.audio_service:
                self.audio_service.stop_recording()
            if self.visual_summarizer:
                self.visual_summarizer.stop()
            if self.audio_summarizer:
                self.audio_summarizer.stop()

def main():
    parser = argparse.ArgumentParser(description="macOS Activity Logger")
    parser.add_argument("--interval", type=float, default=2.0, help="Capture interval in seconds")
    parser.add_argument("--threshold", type=float, default=95.0, help="Similarity threshold percentage")
    parser.add_argument("--logs-dir", type=str, default="logs", help="Directory to save logs")
    parser.add_argument("--no-audio", action="store_true", help="Disable audio recording")
    # For background summarization if needed
    parser.add_argument("--summarize", action="store_true", help="Enable background summarization (Visual & Audio)")
    parser.add_argument("--summary-chunk-size", type=int, default=10, help="Number of items per summary chunk")
    
    args = parser.parse_args()

    # Inverted logic for apps that expect 'no_summarize'
    args.no_summarize = not args.summarize
    
    app = ActivityLoggerApp(args)
    app.run()


if __name__ == "__main__":
    main()
