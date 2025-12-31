import sys
import os
from datetime import datetime

# srcをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from logger.infrastructure.mac_os.screen import ScreenCapturer
from logger.infrastructure.mac_os.vision import OcrService
from logger.infrastructure.mac_os.accessibility import WindowInfoService
from logger.domain.services import SimilarityChecker

def main():
    print("=== macOS Activity Logger Verification ===")
    
    # 1. Active Window
    print("\n[Action] Getting Active Window...")
    window_service = WindowInfoService()
    window_info = window_service.get_active_window_title()
    print(f"  -> App: {window_info['app']}")
    print(f"  -> Title: {window_info['title']}")
    if window_info['app'] == "Unknown":
        print("  [!] Accessibility permission might be missing.")

    # 2. Screen Capture
    print("\n[Action] Capturing Screen...")
    screen_capturer = ScreenCapturer()
    image_ref = screen_capturer.capture_screen()
    if image_ref:
        print("  -> Capture Success (CGImageRef obtained)")
    else:
        print("  -> Capture Failed")
        return

    # 3. Resize / Similarity Check
    print("\n[Action] Resizing for comparison...")
    img_data = screen_capturer.resize_for_comparison(image_ref)
    print(f"  -> Resized shape: {img_data.shape}")
    
    sim_checker = SimilarityChecker()
    # 自分自身と比較 (Trueになるはず)
    is_sim = sim_checker.is_similar(img_data, img_data)
    print(f"  -> Self-similarity check: {is_sim} (Expected: True)")

    # 4. OCR
    print("\n[Action] Running OCR (Vision Framework)...")
    ocr_service = OcrService()
    text = ocr_service.extract_text(image_ref)
    print(f"  -> OCR Text Length: {len(text)}")
    print("  -> Preview (first 100 chars):")
    print(f"     {text[:100].replace(chr(10), ' ')}...")

if __name__ == "__main__":
    main()
