import sys
import time
import argparse
import signal
import threading
from datetime import datetime

# srcをパスに追加 (パッケージとしてインストールされていない場合用)
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

from src.logger.application.controller import ActivityLoggerController

class ActivityLoggerApp:
    def __init__(self, args):
        self.args = args
        self.controller = ActivityLoggerController(
            interval=args.interval,
            threshold=args.threshold,
            logs_dir=args.logs_dir,
            no_audio=args.no_audio,
            no_summarize=args.no_summarize,
            summary_chunk_size=args.summary_chunk_size
        )
        # GUIとは異なり、CLIでは標準出力への出力をコールバックで繋ぐ
        self.controller.on_log_entry = self._handle_log_entry
        self.controller.on_error = lambda msg: print(f"⚠️  {msg}")
        self.controller.on_status_change = lambda status: print(f"[*] Status: {status}")

    def _handle_log_entry(self, entry):
        status = "Screen Change" if entry.metadata.get("is_screen_change") else "Static"
        print(f"[{entry.timestamp.strftime('%H:%M:%S')}] [{status}] {entry.screen.app_name} - {entry.screen.window_title[:30]}...")
        if entry.audio_transcript:
            print(f"  > Audio: {entry.audio_transcript}")

    def run(self):
        print(f"Starting monitoring loop (Interval: {self.args.interval}s, Threshold: {self.args.threshold}%)")
        print(f"Logs will be saved to: {self.args.logs_dir}")
        print("Press Ctrl+C to stop.")
        
        self.controller.start()
        
        try:
            # Controllerはバックグラウンドスレッドで動くため、メインスレッドは待機
            while self.controller.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            print("\nStopping logger...")
            self.controller.stop()

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
