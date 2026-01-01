import Vision
from Quartz import CGImageRef

class OcrService:
    """Vision Framework を使用したOCRサービス"""
    
    def __init__(self):
        # VNRecognizeTextRequestの初期化は重いのでコンストラクタで1回だけやる
        self.request = Vision.VNRecognizeTextRequest.alloc().init()
        
        # 認識レベル: 高精度 (Accurate) vs 高速 (Fast)
        # M1/M2/M3/M4チップならAccurateでも十分高速
        self.request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
        
        # 言語設定: 日本語と英語
        # Vision Frameworkは自動判別も優秀だが、指定したほうが精度が良い場合がある
        self.request.setRecognitionLanguages_(["ja-JP", "en-US"])
        
        # 言語補正を使うか (Trueだと辞書マッチングで補正してくれる)
        self.request.setUsesLanguageCorrection_(True)

    def extract_text(self, image_ref: CGImageRef) -> str:
        """
        CGImageRefからテキストを抽出する
        """
        if image_ref is None:
            return ""

        # ハンドラの作成
        handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(
            image_ref, None
        )
        
        # リクエスト実行 (同期処理)
        # MLX(GPU)との競合を避けるため、一応ロックを取る
        try:
            from ..ai.utils import mlx_lock
            with mlx_lock:
                success, error = handler.performRequests_error_([self.request], None)
        except ImportError:
            # Fallback if utils not available in this context
            success, error = handler.performRequests_error_([self.request], None)
        
        if not success:
            # エラーログなどは実運用ではloggerを使うべき
            print(f"OCR Error: {error}")
            return ""

        # 結果の取得
        results = self.request.results()
        if not results:
            return ""
            
        text_lines = []
        for observation in results:
            # observation is VNRecognizedTextObservation
            # bestCandidate(1) でトップ1の候補を取得
            candidates = observation.topCandidates_(1)
            if candidates:
                # VNRecognizedText
                text = candidates[0].string()
                text_lines.append(text)
        
        return "\n".join(text_lines)
