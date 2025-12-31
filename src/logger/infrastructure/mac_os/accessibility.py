from ApplicationServices import (
    AXUIElementCreateSystemWide, 
    AXUIElementCopyAttributeValue,
    AXUIElementCreateApplication,
    kAXFocusedApplicationAttribute, 
    kAXTitleAttribute,
    # kAXWindowsAttribute,
    # kAXRoleAttribute,
    # kAXSubroleAttribute
)
import contextlib

class WindowInfoService:
    """Accessibility API (AXUIElement) を使用したウィンドウ情報取得"""

    def get_active_window_title(self) -> dict:
        """
        現在アクティブな（フォーカスのある）ウィンドウのタイトルとアプリ名を取得する。
        NSWorkspaceはRunLoopがないと更新されないため、Quartzを使用してWindowServerから直接情報を取得する。
        """
        import Quartz
        
        result = {"app": "Unknown", "title": "Unknown"}
        pid = None

        # 1. Quartzを使ってWindowListを取得 (Z-order順)
        # 上位にあるウィンドウの所有アプリ＝アクティブアプリとみなす
        try:
            options = (
                Quartz.kCGWindowListOptionOnScreenOnly | 
                Quartz.kCGWindowListExcludeDesktopElements
            )
            # 全ウィンドウ情報を取得
            window_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)
            
            for window in window_list:
                # レイヤー0 (通常のアプリウィンドウ) を探す
                layer = window.get('kCGWindowLayer', 0)
                owner_name = window.get('kCGWindowOwnerName', '')
                
                # Dock, Window Server, System UI系を除外する簡易フィルタ
                # 必要に応じて除外リストを追加
                if layer == 0 and owner_name and owner_name not in ["Window Server", "Dock"]:
                    result["app"] = owner_name
                    pid = window.get('kCGWindowOwnerPID')
                    break
                    
        except Exception as e:
            print(f"Quartz Error: {e}")

        # 2. PIDからAccessibility APIを使ってウィンドウタイトルを取る
        try:
            if pid:
                # PIDからAXApplicationElementを作成
                app_element = AXUIElementCreateApplication(pid)
                
                # アクティブなウィンドウを取得 (AXFocusedWindow)
                error, focused_window = AXUIElementCopyAttributeValue(
                    app_element, "AXFocusedWindow", None
                )
                
                if error == 0 and focused_window:
                    # ウィンドウのタイトルを取得
                    error, val = AXUIElementCopyAttributeValue(
                        focused_window, kAXTitleAttribute, None
                    )
                    if error == 0:
                        result["title"] = str(val)
                    else:
                        result["title"] = "" # タイトルなし
                else:
                    # ApplicationはあるがFocusedWindowがない場合
                    pass
            else:
                # Quartzで取れなかった場合のフォールバック（従来のAccessibility）
                system_wide = AXUIElementCreateSystemWide()
                error, app_element = AXUIElementCopyAttributeValue(
                    system_wide, kAXFocusedApplicationAttribute, None
                )
                if error == 0 and app_element:
                    error, app_title = AXUIElementCopyAttributeValue(
                        app_element, kAXTitleAttribute, None
                    ) # ここ間違えやすいが kAXTitleAttribute はアプリ名
                    if error == 0:
                        result["app"] = str(app_title)

        except Exception as e:
            # print(f"Accessibility Error: {e}")
            pass
            
        return result
