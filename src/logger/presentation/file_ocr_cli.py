import sys
import os
import argparse
from pathlib import Path

# srcをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

from src.logger.infrastructure.mac_os.vision import OcrService
from src.logger.infrastructure.mac_os.media_loader import MediaLoader

def main():
    parser = argparse.ArgumentParser(description="OCR Tool for Files (PDF, Images)")
    parser.add_argument(
        "--input-dir", 
        type=str, 
        default="/Users/takumi/Documents/src/private_src/mac_logs/data",
        help="Directory containing files to OCR"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory to save OCR results (default: {input_dir}/ocr_result)"
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"Error: Input directory does not exist: {input_dir}")
        sys.exit(1)

    print(f"Processing files in: {input_dir}")

    # 出力ディレクトリの設定
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = input_dir / "ocr_result"
    
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Results will be saved to: {output_dir}")

    # サービスの初期化
    try:
        ocr_service = OcrService()
        media_loader = MediaLoader()
    except Exception as e:
        print(f"Failed to initialize services: {e}")
        sys.exit(1)

    # 対応する拡張子
    supported_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif', '.ico'}

    files = [f for f in input_dir.iterdir() if f.is_file() and f.suffix.lower() in supported_extensions]
    
    if not files:
        print("No supported files found.")
        return

    for file_path in files:
        print(f"Processing: {file_path.name}...")
        
        output_path = output_dir / file_path.with_suffix('.txt').name
        full_text = []
        
        try:
            # ページ/画像ごとにOCR実行
            for i, image_ref in enumerate(media_loader.load_images_from_file(str(file_path))):
                text = ocr_service.extract_text(image_ref)
                if text:
                    full_text.append(f"--- Page/Image {i+1} ---\n{text}")
                else:
                    full_text.append(f"--- Page/Image {i+1} ---\n(No text detected)")
            
            if full_text:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write("\n\n".join(full_text))
                print(f"  Saved to: {output_path.name}")
            else:
                print(f"  No text extracted from {file_path.name}")

        except Exception as e:
            print(f"  Error processing {file_path.name}: {e}")

    print("All done.")

if __name__ == "__main__":
    main()
