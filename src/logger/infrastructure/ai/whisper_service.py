import threading
import time
import queue
import numpy as np
import sounddevice as sd
import mlx_whisper

class WhisperAudioService:
    def __init__(self, model_path="mlx-community/whisper-large-v3-turbo", sample_rate=16000, vad_threshold=0.015):
        self.sample_rate = sample_rate
        self.model_path = model_path
        self.vad_threshold = vad_threshold
        
        # Audio Buffer
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.record_stream = None
        
        # Transcription State
        self._transcript_buffer = [] # list of strings
        self._lock = threading.Lock()
        
        # Worker Thread
        self.transcription_thread = None
        self._stop_event = threading.Event()

    def preload_model(self):
        """
        Explicitly load the model (download if necessary) by running a dummy transcription.
        """
        print(f"Preloading Whisper model: {self.model_path}...")
        try:
            # Dummy inference to force model load
            dummy_audio = np.zeros(16000) # 1 second of silence
            mlx_whisper.transcribe(dummy_audio, path_or_hf_repo=self.model_path)
            print("Model loaded successfully.")
        except Exception as e:
            print(f"Failed to preload model: {e}")

    def start_recording(self):
        if self.is_recording:
            return
            
        print(f"Starting WhisperAudioService with model: {self.model_path}")
        
        # 1. Start Recording Stream (Callback based)
        def callback(indata, frames, time, status):
            if status:
                print(f"[WARN] SoundDevice Status: {status}")
            # indata is (frames, channels), we want (frames,) mono
            # copy() is important because indata is reused
            self.audio_queue.put(indata[:, 0].copy())

        # input_device_index=None uses system default
        self.record_stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            callback=callback,
            blocksize=int(self.sample_rate * 5.0) # 5 seconds chunks for crude VAD/batching
        )
        self.record_stream.start()
        
        # 2. Start Transcription Worker
        self._stop_event.clear()
        self.transcription_thread = threading.Thread(target=self._transcription_loop)
        self.transcription_thread.daemon = True
        self.transcription_thread.start()
        
        self.is_recording = True
        print("Audio recording and transcription service started.")

    def stop_recording(self):
        if self.is_recording:
            # Stop Worker
            self._stop_event.set()
            if self.transcription_thread:
                self.transcription_thread.join(timeout=5.0)
            
            # Stop Stream
            if self.record_stream:
                self.record_stream.stop()
                self.record_stream.close()
            
            self.is_recording = False
            print("Audio recording stopped.")

    def _transcription_loop(self):
        """
        Consumes audio chunks from queue and runs mlx-whisper.
        Using a simple approach: Transcribe every ~5-10 seconds of audio.
        """
        accumulated_audio = []
        accumulated_samples = 0
        min_seconds_to_transcribe = 5.0 # Transcribe when we have at least 5s
        
        while not self._stop_event.is_set():
            try:
                # Wait for audio data (timeout allows check for stop_event)
                chunk = self.audio_queue.get(timeout=1.0)
                accumulated_audio.append(chunk)
                accumulated_samples += len(chunk)
                
                # Check if we have enough to transcribe
                current_duration = accumulated_samples / self.sample_rate
                
                if current_duration >= min_seconds_to_transcribe:
                    self._process_accumulated_audio(accumulated_audio)
                    accumulated_audio = []
                    accumulated_samples = 0
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in transcription loop: {e}")

        # Process remaining audio on stop
        if accumulated_audio:
            self._process_accumulated_audio(accumulated_audio)

    def _calculate_rms(self, audio_data):
        """Calculate Root Mean Square amplitude."""
        if len(audio_data) == 0:
            return 0.0
        return np.sqrt(np.mean(audio_data**2))

    def _is_hallucination(self, text):
        """
        Simple heuristic logic to filter known Whisper hallucinations.
        """
        text = text.strip()
        if not text:
            return False
            
        # 1. Repetitive patterns check (e.g., "DoDoDoDo...", "パパパパ...")
        if len(text) > 10:
            # Check for single character repetition dominating the string
            char_counts = {}
            for char in text:
                char_counts[char] = char_counts.get(char, 0) + 1
            
            max_count = max(char_counts.values())
            if max_count / len(text) > 0.5: # 50% same character? suspicious
                # Further check: repetitive substrings
                return True

        # 2. Known hallucination phrases (often generated during silence)
        known_hallucinations = [
            "ご視聴ありがとうございました",
            "チャンネル登録",
            "字幕",
            "Subtitles",
            "Thank you for watching"
        ]
        
        for phrase in known_hallucinations:
            if phrase in text:
                return True
                
        return False

    def _process_accumulated_audio(self, audio_chunks):
        """
        Merge chunks and run Whisper
        """
        if not audio_chunks:
            return
            
        # Concatenate numpy arrays
        audio_data = np.concatenate(audio_chunks)
        
        # 1. VAD Check (RMS)
        rms = self._calculate_rms(audio_data)
        # print(f"[DEBUG] Audio RMS: {rms:.4f}")
        
        if rms < self.vad_threshold:
            # Silence detected, skip transcription
            return

        # Run Transcription
        # mlx_whisper.transcribe supports numpy array directly
        try:
            # print(f"[DEBUG] Transcribing {len(audio_data)/self.sample_rate:.1f}s of audio...")
            result = mlx_whisper.transcribe(
                audio_data, 
                path_or_hf_repo=self.model_path,
                language="ja", # Auto-detect is slower, enforcing Japanese is safer for this user
                verbose=False
            )
            text = result["text"].strip()
            
            # 2. Post-processing / Hallucination Filter
            if text and not self._is_hallucination(text):
                print(f"[Whisper] {text}")
                with self._lock:
                    self._transcript_buffer.append(text)
            elif text:
                print(f"[Whisper Filtered] Hallucination/Noise detected: {text[:30]}...")
                    
        except Exception as e:
            print(f"Whisper Transcription Failed: {e}")

    def get_transcript_chunk(self) -> str:
        """
        Returns and clears the latest transcribed text.
        """
        with self._lock:
            if not self._transcript_buffer:
                return ""
            
            # Join all pending texts
            full_text = " ".join(self._transcript_buffer)
            self._transcript_buffer = [] # Clear consumed
            return full_text
