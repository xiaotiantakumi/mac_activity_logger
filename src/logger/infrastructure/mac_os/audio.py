import threading
import AVFoundation
import Speech
from Cocoa import NSLocale

class AudioService:
    def __init__(self, locale="ja-JP"):
        self.locale = NSLocale.localeWithLocaleIdentifier_(locale)
        self.recognizer = Speech.SFSpeechRecognizer.alloc().initWithLocale_(self.locale)
        self.audio_engine = AVFoundation.AVAudioEngine.alloc().init()
        self.recognition_request = None
        self.recognition_task = None
        
        # 文字起こし結果を一時保存するバッファ
        self._transcript_buffer = []
        self._lock = threading.Lock()
        self.is_running = False

    def start_recording(self):
        """音声認識を開始する"""
        if self.is_running:
            return

        # 権限状況の確認
        status = Speech.SFSpeechRecognizer.authorizationStatus()
        print(f"[DEBUG] SFSpeechRecognizer Authorization Status: {status} (3=Authorized, 2=Denied, 1=Restricted, 0=NotDetermined)")
        
        if status != 3: # Authorized
            # CLIではrequestAuthorizationのブロックが呼ばれないことがあるが、
            # 呼び出しておくとTCCプロンプトが出るトリガーになる場合がある
            # Speech.SFSpeechRecognizer.requestAuthorization_(lambda status: print(f"Auth Updated: {status}"))
            pass

        # 既存のタスクがあればキャンセル
        if self.recognition_task:
            self.recognition_task.cancel()
            self.recognition_task = None

        # AudioSessionの設定
        # CLIツールの場合、AVAudioSessionはiOSほど厳密ではないが、InputNodeを使うためにEngineを準備

        self.recognition_request = Speech.SFSpeechAudioBufferRecognitionRequest.alloc().init()
        
        input_node = self.audio_engine.inputNode()
        if not input_node:
            print("Audio Input Node not found.")
            return

        self.recognition_request.setShouldReportPartialResults_(True)

        # 認識タスクの開始
        def result_handler(result, error):
            if error:
                print(f"[DEBUG] Recognition Error: {error}")
                self.is_running = False
                return
            
            if result:
                text = result.bestTranscription().formattedString()
                print(f"[DEBUG] Recognition Update: {text}") 
                with self._lock:
                    self._current_live_text = text

        # ブロックをPythonの関数として渡すため、PyObjCのシグネチャに合うように自動変換される
        self.recognition_task = self.recognizer.recognitionTaskWithRequest_resultHandler_(
            self.recognition_request, result_handler
        )

        self._current_live_text = ""
        self._last_consumed_text_len = 0 

        # マイク入力を認識リクエストに流し込むフォーマット設定
        recording_format = input_node.outputFormatForBus_(0)
        
        def audio_tap_block(buffer, time):
            print(f"[DEBUG] Audio Buffer Received: {buffer.frameLength()} frames")
            self.recognition_request.appendAudioPCMBuffer_(buffer)

        input_node.installTapOnBus_bufferSize_format_block_(0, 1024, recording_format, audio_tap_block)

        self.audio_engine.prepare()
        success, error = self.audio_engine.startAndReturnError_(None)
        if not success:
            print(f"Audio Engine Start Error: {error}")
            return

        self.is_running = True
        print("Audio recording started.")

    def stop_recording(self):
        """音声認識を停止する"""
        if self.audio_engine.isRunning():
            self.audio_engine.stop()
            self.audio_engine.inputNode().removeTapOnBus_(0)
            self.recognition_request.endAudio()
            self.is_running = False
            print("Audio recording stopped.")

    def get_transcript_chunk(self) -> str:
        """
        前回の呼び出し以降に認識されたテキストの増分を取得する。
        注意: SFSpeechRecognizerは修正が入ると文字列が変わるため、単純なスライスでは整合性が取れない場合がある。
        より高度な実装では isFinal を待つべきだが、リアルタイム性を重視して最新の状態を返す。
        """
        with self._lock:
            full_text = self._current_live_text
            # 前回取得した長さより長くなっていれば、その差分を返す
            if len(full_text) > self._last_consumed_text_len:
                chunk = full_text[self._last_consumed_text_len:]
                self._last_consumed_text_len = len(full_text)
                return chunk
            return ""

    # 簡易リセット（長時間の動作でメモリが溢れないように定期的・または無音区間でリセットしたい場合に使用）
    def reset_buffer(self):
        with self._lock:
            self._current_live_text = ""
            self._last_consumed_text_len = 0
