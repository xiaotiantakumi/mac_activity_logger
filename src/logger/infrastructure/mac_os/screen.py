import Quartz
import numpy as np
from Cocoa import NSBitmapImageRep
# from CoreFoundation import CFDataGetBytePtr, CFDataGetLength # 必要であれば使う

class ScreenCapturer:
    """Quartz (CoreGraphics) を使用したスクリーンキャプチャ"""
    
    def capture_screen(self):
        """
        画面全体をキャプチャし、CGImageRefを返す。
        ファイルには保存せず、メモリ上で完結する。
        """
        # メインディスプレイのバウンドを取得（マルチモニタ対応は今後の課題）
        # kCGWindowListOptionOnScreenOnly: 画面上のウィンドウのみ
        # kCGNullWindowID: 全てのウィンドウ
        image_ref = Quartz.CGWindowListCreateImage(
            Quartz.CGRectInfinite,
            Quartz.kCGWindowListOptionOnScreenOnly,
            Quartz.kCGNullWindowID,
            Quartz.kCGWindowImageDefault
        )
        return image_ref

    def resize_for_comparison(self, image_ref, target_size=(100, 100)) -> np.ndarray:
        """
        類似度比較用に画像を小さくリサイズし、Numpy配列として返す。
        """
        if image_ref is None:
            return np.zeros((target_size[1], target_size[0], 4), dtype=np.uint8)

        width = Quartz.CGImageGetWidth(image_ref)
        height = Quartz.CGImageGetHeight(image_ref)
        
        # NSBitmapImageRepを作成してビットマップデータにアクセス
        rep = NSBitmapImageRep.alloc().initWithCGImage_(image_ref)
        if rep is None:
             return np.zeros((target_size[1], target_size[0], 4), dtype=np.uint8)

        # bitmapData() は python bytes を返す (PyObjCのバージョンによるが通常はそう)
        # bufferプロトコル対応オブジェクトが返ることを期待
        bitmap_data = rep.bitmapData()
        
        # データの長さを計算 (width * height * 4 channels)
        # 実際には bytesPerRow * height だが、packedなら w*h*4
        expected_size = width * height * 4
        
        # numpy配列化
        try:
            # np.frombufferは参照のみ作成するため、必ずcopy()してデータをPython側に保持させる
            # これをしないと、repがGCされた後にメモリアクセス違反(SegFault)になる可能性がある
            arr = np.frombuffer(bitmap_data, dtype=np.uint8).copy()
            
            # アルファチャンネルがない場合など、サイズが合わない可能性への対処
            # ここではRGBA(4ch)を前提とするが、RGB(3ch)の場合も考慮が必要かも
            # いったんリシェイプを試みる
            
            # strideなどを考慮せず、単純にフラットな配列として扱い、スライスで間引く戦略
            # 形状復元: (height, width, channels)
            # CoreGraphicsのデフォルトはARGBやRGBAだが、計算には「変化」だけ見ればいいので
            # チャンネル順序は厳密でなくても比較さえできれば良い
            
            # バッファサイズが足りない/多い場合のガード
            if len(arr) < expected_size:
                # 失敗時
                return np.zeros((target_size[1], target_size[0], 4), dtype=np.uint8)
                
            arr = arr[:expected_size] # 余分なパディング等は無視（危険だが高速化重視）
            arr = arr.reshape((height, width, 4))
            
            # スライスで簡易リサイズ
            # cv2.resizeなどは重いし遅いので、numpyのスライシングで間引く
            step_x = max(1, width // target_size[0])
            step_y = max(1, height // target_size[1])
            
            resized_arr = arr[::step_y, ::step_x, :]
            
            # target_sizeぴったりにならない場合があるので、カットする
            resized_arr = resized_arr[:target_size[1], :target_size[0], :]
            
            return resized_arr
            
        except Exception as e:
            print(f"Resize Error: {e}")
            return np.zeros((target_size[1], target_size[0], 4), dtype=np.uint8)
