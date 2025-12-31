import numpy as np
from typing import Optional

class SimilarityChecker:
    """
    連続するフレーム（画像）が「類似しているか（変化がないか）」を判定するドメインサービス。
    """
    def __init__(self, threshold_percent: float = 95.0):
        """
        Args:
            threshold_percent: 一致率の閾値 (0.0 - 100.0)。
                             この値以上の類似度であれば「変化なし」とみなす。
        """
        self.threshold = threshold_percent

    def is_similar(self, current_img_data: Optional[np.ndarray], previous_img_data: Optional[np.ndarray]) -> bool:
        """
        2つの画像データを比較し、類似しているかを返す。
        
        Args:
            current_img_data: 現在のフレームの画像データ (numpy array)
            previous_img_data: 1つ前のフレームの画像データ (numpy array)
            
        Returns:
            bool: 類似していれば True (スキップ対象), 違っていれば False (記録対象)
        """
        if current_img_data is None or previous_img_data is None:
            # どちらかが欠けている場合は「比較不能」として False (記録する) を返すのが安全
            # ただし、初回起動時(previous is None)は記録したいので False でOK
            return False
            
        # 形状が違う場合は比較不可（リサイズ設定が変わった時など）
        if current_img_data.shape != previous_img_data.shape:
            return False

        # 差分計算 (絶対差分)
        # int型にキャストしてから差分を取ることでオーバーフローを防ぐ
        diff = np.abs(current_img_data.astype(int) - previous_img_data.astype(int))
        
        # 平均差分を計算
        # 0 (完全一致) 〜 255 (完全不一致)
        mean_diff = np.mean(diff)
        
        # 許容される誤差の計算
        # 例: threshold=95% なら、残り5%の不一致まで許容
        # 255 * 0.05 = 12.75
        allowance = 255 * (1 - (self.threshold / 100.0))
        
        # 平均差分が許容値以下なら「類似している」
        return mean_diff < allowance
