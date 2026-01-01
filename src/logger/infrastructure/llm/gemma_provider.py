import json
import logging
from typing import Optional, Any
from mlx_lm import load, generate
from ...domain.interfaces import LlmProvider

# Set up logging for MLX (it can be chatty)
logging.getLogger("mlx_lm").setLevel(logging.INFO)

class GemmaLlmProvider(LlmProvider):
    # Default model ID matching the download script
    DEFAULT_MODEL = "mlx-community/gemma-2-2b-it-4bit"

    def __init__(self, model_id: str = None):
        self.model_id = model_id or self.DEFAULT_MODEL
        print(f"Loading local model: {self.model_id}...")
        try:
            self.model, self.tokenizer = load(self.model_id)
            print("Model loaded successfully.")
        except Exception as e:
            print(f"Failed to load model {self.model_id}: {e}")
            raise

    def process_content(self, prompt: str) -> Optional[Any]:
        try:
            messages = [{"role": "user", "content": prompt}]
            if hasattr(self.tokenizer, "apply_chat_template") and self.tokenizer.chat_template:
                formatted_prompt = self.tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True
                )
            else:
                formatted_prompt = f"User: {prompt}\n\nModel:"

            # Use global lock to prevent concurrency with Whisper
            from ..ai.utils import mlx_lock
            print(f"[LLM] Waiting for lock...")
            with mlx_lock:
                print(f"[LLM] Lock acquired. Generating...")
                response_text = generate(
                    self.model,
                    self.tokenizer,
                    prompt=formatted_prompt,
                    max_tokens=2048, # Lowered from 4096 to prevent runaway
                    verbose=False
                )
                print(f"[LLM] Generation finished. Releasing lock...")

            # Clean up response (Markdown code blocks)
            cleaned_text = response_text.strip()
            
            # Try to find a JSON block within the response
            # Some models wrap JSON in code blocks, others add commentary
            json_start = cleaned_text.find('{')
            json_end = cleaned_text.rfind('}')
            
            if json_start != -1 and json_end != -1 and json_end > json_start:
                potential_json = cleaned_text[json_start:json_end+1]
                try:
                    return json.loads(potential_json)
                except json.JSONDecodeError:
                    # If extraction failed, fall back to literal or whole text
                    pass
            
            # If no JSON object found, return as string
            return cleaned_text

        except Exception as e:
            print(f"Gemma inference error: {e}")
            return None
