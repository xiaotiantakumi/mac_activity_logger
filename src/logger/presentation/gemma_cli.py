import sys
import os
import argparse

# Add src to python path if needed (for direct execution)
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../"))

from src.logger.infrastructure.llm.gemma_provider import GemmaLlmProvider
from src.logger.application.summarization_use_case import LogSummarizationUseCase

def main():
    parser = argparse.ArgumentParser(description="Gemma Chat & Summarization CLI")
    parser.add_argument("prompt", type=str, nargs="?", help="Input prompt")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    parser.add_argument("--summarize", "-s", action="store_true", help="Run log summarization for existing logs")
    parser.add_argument("--logs-dir", type=str, default="logs", help="Directory containing logs")
    parser.add_argument("--chunk-size", type=int, default=10, help="Chunk size for summarization")
    args = parser.parse_args()

    try:
        print("Loading Gemma model...")
        llm = GemmaLlmProvider()
        print("Model loaded.")

        if args.summarize:
            print(f"Starting one-time summarization for logs in {args.logs_dir}...")
            # Visual Summarizer
            vis = LogSummarizationUseCase(llm, summary_type="visual", logs_root_dir=args.logs_dir)
            vis.run_once(chunk_size=args.chunk_size)
            
            # Audio Summarizer
            aud = LogSummarizationUseCase(llm, summary_type="audio", logs_root_dir=args.logs_dir)
            aud.run_once(chunk_size=args.chunk_size)
            print("Summarization complete.")
            return

        if args.interactive:
            print("Starting interactive chat. Type 'quit' or 'exit' to stop.")
            while True:
                try:
                    user_input = input("\nYou: ")
                    if user_input.lower() in ["quit", "exit"]:
                        break
                    if not user_input.strip():
                        continue
                        
                    print("Gemma: ", end="", flush=True)
                    response = llm.process_content(user_input) # Use process_content as in provider
                    print(response)
                except KeyboardInterrupt:
                    break
        elif args.prompt:
            response = llm.process_content(args.prompt)
            print(response)
        else:
            # Read from stdin
            if not sys.stdin.isatty():
                prompt = sys.stdin.read()
                response = llm.process_content(prompt)
                print(response)
            else:
                parser.print_help()
                
    except KeyboardInterrupt:
        print("\nAborted.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
