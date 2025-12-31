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

# AppKit (NSRunLoop) 不使用になったため削除
# from AppKit import NSRunLoop, NSDate

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

    def monitoring_loop(self):
        """
        Main Loop for Screen Monitoring.
        Since SoundDevice uses its own threads, we can run this in the main thread now
        or keep it separate. For simplicity and allowing clean Ctrl+C, 
        running this in the main thread (blocking sleep) is easiest.
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
                    print(f"[{entry.timestamp.strftime('%H:%M:%S')}] Logged: {entry.screen.app_name} - {entry.screen.window_title[:30]}...")
                    if transcript:
                        print(f"  > Audio: {transcript}")
                elif transcript:
                     # 画面変化がなくても音声があった場合はログに出したい需要があるかもしれないが
                     # 現状のUseCase仕様では「画面変化なし=None」なので、
                     # ここではコンソールにだけ出しておくか、UseCase側で処理すべき議論がある。
                     # ですが、今回は「画面ログに音声を付与」なので、画面変化なしならログに落ちない仕様を維持。
                     pass

            except Exception as e:
                print(f"Error in monitoring loop: {e}")
            
            elapsed = time.time() - start_time
            sleep_time = max(0, self.args.interval - elapsed)
            
            # sleepを分割してCtrl+Cの反応を良くする
            # (time.sleepはシグナルで中断されるはずだが念のため)
            time.sleep(sleep_time)

    def run(self):
        # 0. Preload Model (Download & Warmup)
        # This prevents the first transcription from being very slow or timing out
        if self.audio_service:
            self.audio_service.preload_model()

        # 1. Start Audio Service
        if self.audio_service:
            try:
                self.audio_service.start_recording()
            except Exception as e:
                print(f"Failed to start audio service: {e}")
                print("Continuing without audio log...")

        # 2. Run Monitoring Loop (Blocking)
        try:
            self.monitoring_loop()
        except KeyboardInterrupt:
            # monitoring_loop内のsleep等でキャッチされる想定
            pass
        finally:
            self.should_stop = True
            print("\nStopping logger...")
            if self.audio_service:
                self.audio_service.stop_recording()

def main():
    parser = argparse.ArgumentParser(description="macOS Activity Logger")
    parser.add_argument("--interval", type=float, default=2.0, help="Capture interval in seconds")
    parser.add_argument("--threshold", type=float, default=95.0, help="Similarity threshold percentage")
    parser.add_argument("--logs-dir", type=str, default="logs", help="Directory to save logs")
    parser.add_argument("--no-audio", action="store_true", help="Disable audio recording")
    args = parser.parse_args()

    app = ActivityLoggerApp(args)
    app.run()


if __name__ == "__main__":
    main()
