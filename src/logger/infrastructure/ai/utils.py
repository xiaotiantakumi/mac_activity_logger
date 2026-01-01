import threading

# Global lock to serialize heavy MLX inference (Whisper and LLM)
# to prevent memory pressure or Metal context conflicts on Apple Silicon.
mlx_lock = threading.Lock()
