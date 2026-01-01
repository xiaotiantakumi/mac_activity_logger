import os
import json
import time
import logging
import threading
from datetime import datetime
from typing import Dict, List, Any
from ..domain.interfaces import LlmProvider

# Setup specific logger for summarization system
sys_logger = logging.getLogger("system_summarizer")
sys_logger.setLevel(logging.INFO)
# We assume basicConfig or similar is set up, or we can add a file handler here.
# For now, we'll setup a file handler if not exists
log_file_path = "logs/system_summarizer.log"
os.makedirs("logs", exist_ok=True)
file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
sys_logger.addHandler(file_handler)

class LogSummarizationUseCase:
    def __init__(self, llm_provider: LlmProvider, summary_type: str = "combined", logs_root_dir: str = "logs"):
        self.llm = llm_provider
        self.summary_type = summary_type # "combined", "visual", "audio"
        self.logs_root_dir = logs_root_dir
        self.state_file = os.path.join(logs_root_dir, f"summarizer_state_{summary_type}.json")
        self.state = self._load_state()
        self.should_stop = False

    def _load_state(self) -> Dict[str, int]:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                sys_logger.error(f"Failed to load state for {self.summary_type}: {e}")
        return {}

    def _save_state(self):
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            sys_logger.error(f"Failed to save state for {self.summary_type}: {e}")

    def start_monitoring(self, chunk_size: int = 5, check_interval: float = 10.0):
        sys_logger.info(f"Starting {self.summary_type} summarization monitoring (chunk_size={chunk_size})...")
        while not self.should_stop:
            try:
                self._scan_and_process(chunk_size)
            except Exception as e:
                sys_logger.error(f"Error in {self.summary_type} monitoring loop: {e}", exc_info=True)
            
            time.sleep(check_interval)

    def run_once(self, chunk_size: int = 5):
        """
        Runs the summarization process once for all available logs.
        """
        sys_logger.info(f"Running one-time {self.summary_type} summarization (chunk_size={chunk_size})...")
        try:
            self._scan_and_process(chunk_size)
        except Exception as e:
            sys_logger.error(f"Error in {self.summary_type} run_once: {e}", exc_info=True)

    def stop(self):
        self.should_stop = True

    def _scan_and_process(self, chunk_size: int):
        if not os.path.exists(self.logs_root_dir):
            return

        dirs = sorted([d for d in os.listdir(self.logs_root_dir) if os.path.isdir(os.path.join(self.logs_root_dir, d))])

        for date_str in dirs:
            try:
                datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                continue

            self._process_directory(date_str, chunk_size)

    def _is_entry_relevant(self, entry: Dict[str, Any]) -> bool:
        if self.summary_type == "visual":
            return entry.get("metadata", {}).get("is_screen_change", False)
        elif self.summary_type == "audio":
            transcript = entry.get("audio", {}).get("transcript", "").strip()
            return bool(transcript)
        return True # combined

    def _process_directory(self, date_str: str, chunk_size: int):
        dir_path = os.path.join(self.logs_root_dir, date_str)
        log_file = os.path.join(dir_path, "activity.jsonl")
        
        # Output filename depends on type
        output_name = "summary.jsonl" if self.summary_type == "combined" else f"{self.summary_type}_summary.jsonl"
        summary_file = os.path.join(dir_path, output_name)

        if not os.path.exists(log_file):
            return

        # processed_count represents the number of RAW lines read from activity.jsonl
        processed_count = self.state.get(date_str, 0)
        
        relevant_entries = []
        raw_line_count = 0
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    raw_line_count += 1
                    if raw_line_count > processed_count:
                        try:
                            entry = json.loads(line)
                            if self._is_entry_relevant(entry):
                                # Tag entry with its raw line index to update state correctly
                                entry["_raw_index"] = raw_line_count
                                relevant_entries.append(entry)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            sys_logger.error(f"Error reading log file {log_file}: {e}")
            return

        # Process chunks from relevant_entries
        while len(relevant_entries) >= chunk_size:
            chunk = relevant_entries[:chunk_size]
            relevant_entries = relevant_entries[chunk_size:]
            
            summary = self._generate_summary(chunk)
            if summary:
                self._append_summary(summary_file, summary)
                # update state to the raw index of the last entry in this chunk
                new_processed_count = chunk[-1]["_raw_index"]
                self.state[date_str] = new_processed_count
                self._save_state()

    def _generate_summary(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not entries:
            return None

        # Create a prompt
        log_text = ""
        start_time = entries[0]['timestamp']
        end_time = entries[-1]['timestamp']

        for e in entries:
            ts = e.get('timestamp', '')[11:19] # Extract HH:MM:SS
            app = e.get('screen', {}).get('app_name', 'Unknown')
            title = e.get('screen', {}).get('window_title', '')
            ocr = e.get('screen', {}).get('ocr_text', '')[:150].replace('\n', ' ') 
            audio = e.get('audio', {}).get('transcript', '')[:150] 
            
            log_text += f"[{ts}] App: {app}, Title: {title}\n"
            if ocr:
                log_text += f"OCR: {ocr}\n"
            if audio:
                log_text += f"Audio: {audio}\n"
            log_text += "---\n"

        # Load prompt from file based on type
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
            
            if self.summary_type == "visual":
                p_name = "summarize_visual_activity.txt"
            elif self.summary_type == "audio":
                p_name = "summarize_audio_activity.txt"
            else:
                p_name = "summarize_daily_activity.txt"
                
            prompt_path = os.path.join(base_dir, "resources", "prompts", p_name)
            
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt_content = f.read()

            prompt = prompt_content.replace("{start_time}", start_time) \
                                   .replace("{end_time}", end_time) \
                                   .replace("{log_text}", log_text)
        except Exception as e:
            sys_logger.error(f"Failed to load prompt template for {self.summary_type}: {e}")
            prompt = f"Summarize {self.summary_type} logs from {start_time} to {end_time}. Logs:\n{log_text}\nJSON Summary:"

        sys_logger.info(f"Generating {self.summary_type} summary ({start_time} - {end_time})...")
        
        for attempt in range(2): 
            response = self.llm.process_content(prompt)
            if response:
                sys_logger.info(f"{self.summary_type.capitalize()} summary generated.")
                if isinstance(response, dict):
                    res_summary = response.get("summary", str(response))
                    return {
                        "timestamp_start": start_time,
                        "timestamp_end": end_time,
                        "summary": res_summary
                    }
                elif isinstance(response, str):
                    return {
                        "timestamp_start": start_time,
                        "timestamp_end": end_time,
                        "summary": response
                    }
            
        sys_logger.warning(f"Failed to generate {self.summary_type} summary after retries.")
        return {
            "timestamp_start": start_time,
            "timestamp_end": end_time,
            "summary": "Failed to generate summary."
        }

    def _append_summary(self, filepath: str, data: Dict[str, Any]):
        try:
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
            sys_logger.info(f"Appended summary to {filepath}")
        except Exception as e:
            sys_logger.error(f"Failed to write summary: {e}")
