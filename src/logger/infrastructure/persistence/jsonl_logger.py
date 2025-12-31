import json
import os
from datetime import datetime
from ...application.interfaces import PersistenceInterface
from ...domain.entities import LogEntry

class JsonlLogger(PersistenceInterface):
    """JSONL形式でローカルファイルに追記するロガー"""
    
    def __init__(self, output_dir: str = "logs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def _get_log_filepath(self, dt: datetime) -> str:
        # 日ごとにローテーション
        filename = f"activity_{dt.strftime('%Y-%m-%d')}.jsonl"
        return os.path.join(self.output_dir, filename)

    def save(self, entry: LogEntry):
        filepath = self._get_log_filepath(entry.timestamp)
        data = entry.to_dict()
        
        # datetime needs serialization helper if not isoformatted in to_dict
        # LogEntry.to_dict() already does isoformat() for timestamp
        
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
