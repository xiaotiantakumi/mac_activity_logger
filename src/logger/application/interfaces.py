from abc import ABC, abstractmethod
from typing import Dict, Any
import numpy as np
from ..domain.entities import LogEntry, ScreenData
from Quartz import CGImageRef

class ScreenCaptureInterface(ABC):
    @abstractmethod
    def capture_screen(self) -> Any: # Returns CGImageRef
        pass

    @abstractmethod
    def resize_for_comparison(self, image_ref: Any, target_size=(100, 100)) -> np.ndarray:
        pass

class OcrInterface(ABC):
    @abstractmethod
    def extract_text(self, image_ref: Any) -> str:
        pass

class WindowInfoInterface(ABC):
    @abstractmethod
    def get_active_window_title(self) -> Dict[str, str]:
        pass

class PersistenceInterface(ABC):
    @abstractmethod
    def save(self, entry: LogEntry):
        pass
