from abc import ABC, abstractmethod
from typing import Optional, Any

class LlmProvider(ABC):
    """
    Interface for LLM services (e.g. Gemma, OpenAI).
    """
    @abstractmethod
    def process_content(self, prompt: str) -> Optional[Any]:
        """
        Sends a prompt to the LLM and returns the response.
        """
        pass
